# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import os
from ddf_utils.str import to_concept_id
from ddf_utils.index import create_index_file


# configuration of file path
source = '../source/AIDSinfo_2014_en.csv'
out_dir = '../../'


def extract_concepts(data):
    conc = data[['cname', 'Unit']].copy()
    conc = conc.drop_duplicates()
    conc.columns = ['name', 'unit']
    conc['concept_type'] = 'measure'
    conc['concept'] = conc['name'].map(lambda x: to_concept_id(x, '[/ -\\.\\*";:]+'))

    # manually create discrete concepts
    disc = pd.DataFrame([['Name', np.nan, 'string', 'name'],
                        ['Year', 'year', 'time', 'year'],
                        ['Area', np.nan, 'entity_domain', 'area'],
                        ['Unit', np.nan, 'string', 'unit']],
                        columns=conc.columns)

    concept = pd.concat([disc, conc])

    return concept[['concept', 'name', 'concept_type', 'unit']]


def extract_entities_area(data):
    area = data[['Area ID', 'Area']].copy()
    area.columns = ['area', 'name']
    area['area'] = area['area'].map(to_concept_id)
    return area.drop_duplicates().sort_values(by='name')


def extract_datapoints(data):
    dps = data[['cname', 'Time Period', 'Area ID', 'Data Value']].copy()
    dps.columns = ['concept', 'year', 'area', 'data']
    dps['area'] = dps['area'].map(to_concept_id)
    dps['concept'] = dps['concept'].map(lambda x: to_concept_id(x, '[/ -\\.\\*";:]+'))
    dps_gps = dps.groupby(by='concept')

    for k, idx in dps_gps.groups.items():
        df = dps.ix[idx][['year', 'area', 'data']].copy()
        df.columns = ['year', 'area', k]

        # assert(np.all(df[['year', 'area']].duplicated()) == False)

        df = df.sort_values(by=['area', 'year'])

        yield k, df

if __name__ == '__main__':
    print('reading source files...')
    data = pd.read_csv(source)

    # strip spaces in the indicator field.
    data['Indicator'] = data['Indicator'].str.strip()

    # change some of entities names, to limit them in alphanumeric
    idx1 = data.query("Subgroup == '25+'").index
    idx2 = data.query("Subgroup == '< 25'").index

    data.loc[idx1, 'Subgroup'] = '25plus'
    data.loc[idx2, 'Subgroup'] = 'below25'

    # combine indicator and subgroup to make concept in this repo.
    # TODO: to confirm if subgroup should be in entities.
    data['cname'] = data['Indicator'] + ' ' + data['Subgroup']

    print('creating concept files...')
    concepts = extract_concepts(data)
    path = os.path.join(out_dir, 'ddf--concepts.csv')
    concepts.to_csv(path, index=False)

    print('creating entities files...')
    area = extract_entities_area(data)
    path = os.path.join(out_dir, 'ddf--entities--area.csv')
    area.to_csv(path, index=False)

    print('creating datapoints files...')
    for k, df in extract_datapoints(data):
        path = os.path.join(out_dir, 'ddf--datapoints--{}--by--area--year.csv'.format(k))
        df.to_csv(path, index=False)

    print('creating index file...')
    create_index_file(out_dir)

    print('Done.')





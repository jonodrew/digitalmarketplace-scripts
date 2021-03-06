import pandas

from dmscripts.models.writecsv import csv_path
from dmscripts.models.modeltrawler import ModelTrawler


def base_model(base_model, keys, get_data_kwargs, client, logger=None, limit=None):
    """Fetch all the data for a given Digital Marketplace model from the api.

    :param base_model: A Digital Marketplace model (client must have a 'find_{model}_iter' method)
    :param keys: The attributes we require of that model.
    :param get_data_kwargs: Additional kwargs for the get request the client will make.
    :param client: Instantiated Digital Marketplace APIClient
    :param logger:
    :param limit: Maximum number of requests for the client to perform.
    :return: A pandas DataFrame of the requested data. Columns as model attributes, rows as instances.
    """
    mt = ModelTrawler(base_model, client)
    data = list(mt.get_data(keys=keys, limit=limit, **get_data_kwargs))
    if logger:
        logger.info(
            '{} {} returned after {}s'.format(len(data), base_model, mt.get_time_running())
        )

    return pandas.DataFrame(data) if data else pandas.DataFrame(columns=keys)


def model(model, directory):
    """Return a Pandas DataFrame loaded from a csv of a given DM model.

    :param model: The model we are working with, used as the name of the .csv
    :param directory: The directory in which to find the model data csv.
    :return: Pandas DataFrame of model data loaded from csv.
    """
    return pandas.read_csv(csv_path(directory, model))


def join(data, model_name, left_on, right_on, directory, how='left', data_duplicate_suffix=None):
    """Left join the model data csv denoted by 'model' to 'data'.

    :param data: The current pandas DataFrame we are working with.
    :param model: The name of a csv in the data directory. This will be joined to data.
    :param left_on: The field in 'data' we are joining on.
    :param right_on: The field in the model csv we are joining on.
    :param directory: The data directory.
    :param how: The type of merge to use. Defaults to 'left'. Can also be 'right', 'inner' or 'outer'.
    :param data_duplicate_suffix: An optional suffix for fields duplicated in both datasets.
    :return: pandas DataFrame of model joined to data.
    """
    csv_to_be_joined = model(model_name, directory)
    return data.merge(
        csv_to_be_joined,
        how=how,
        left_on=left_on,
        right_on=right_on,
        suffixes=[data_duplicate_suffix, '_' + model_name]
    ).fillna('')


def filter_rows(filter_query, data):
    """Filter a pandas DataFrame.

    :param filter_query: The query to apply.
    :param data: The DataFrame to apply the query to.
    :return: pandas DataFrame filtered.
    """
    return data.query(filter_query) if filter_query else data


def process_fields(rules, data):
    for field, fn in rules.items():
        data[field] = data[field].apply(fn)

    return data


def rename_fields(columns, data):
    """Replace any column names using a dict of 'old column name': 'new column name' """
    return data.rename(columns=columns)


def sort_by(columns, data):
    return data.sort_values(by=columns)


def group_by(columns, data):
    return data.groupby(columns).size().reset_index(name='count')


def add_counts(join, group_by, model_name, data, directory):
    left_on, right_on = join
    count_data = model(model_name, directory).groupby(
        [right_on, group_by]
    ).size().reset_index(name='_count')

    for group in count_data[group_by].unique():
        data["{}-{}".format(group_by, group)] = data.merge(
            count_data[count_data[group_by] == group],
            left_on=left_on, right_on=right_on, how='left'
        )['_count'].fillna(0)

    return data


def add_aggregation_counts(data, group_by, join, count_name, query=None):
    """Add aggregated counts to a pandas DataFrame as new columns

    :param data: The DataFrame to apply the new columns to.
    :param group_by: The column whose rows you want to count.
    :param join: How to join the counts back to your data.
    :param count_name: A name for the new column.
    :param query: An optional query to filter counts.
    :return: pandas DataFrame with new count column.
    """
    left_on, right_on = join

    count_data = (data.query(query) if query else data).groupby(group_by)[group_by].count()
    count_data_frame = pandas.DataFrame({group_by: count_data.index, count_name: count_data})

    data = data.merge(count_data_frame, how='left', left_on=left_on, right_on=right_on, suffixes=['', count_name])
    return data


def assign_json_subfields(field, subfields, data):
    """Apply subfields from field to data."""
    for subfield in subfields:
        data[subfield] = data.apply(lambda row: row[field].get(subfield, '') if row[field] else '', axis=1)
    return data


def drop_duplicates(data):
    return data.drop_duplicates()


def duplicate_fields(data, field, new_field_name):
    data[new_field_name] = data[field]
    return data


def get_by_model_fk(config, keys, data, client):
    model = config['model_to_get']
    fk_column_name = config['fk_column_name']
    kwargs = config['get_data_kwargs']

    return_data_frame = pandas.DataFrame()

    if config.get('filter_before_request_query'):
        data = data.query(config['filter_before_request_query']).reset_index(drop=True)
    for id_value in data['id']:
        get_data_kwargs = kwargs.copy()
        get_data_kwargs.update({fk_column_name: id_value})
        model_data = base_model(model, keys, get_data_kwargs, client)
        return_data_frame = return_data_frame.append(model_data, ignore_index=True)

    return pandas.DataFrame(columns=keys) if return_data_frame.empty else return_data_frame

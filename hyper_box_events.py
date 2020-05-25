import argparse
import csv
import json
from datetime import datetime, timedelta, timezone
from dateutil import parser as dateparser, relativedelta
from boxsdk import JWTAuth, Client
from pathlib import Path

from tableauhyperapi import HyperProcess, Telemetry, \
    Connection, CreateMode, \
    NOT_NULLABLE, NULLABLE, SqlType, TableDefinition, \
    Inserter, \
    escape_name, escape_string_literal, \
    TableName, \
    HyperException

# Global variables for the hyper file name, DB Schema and Table
box_hyper_file = 'box_events.hyper'
box_schema = 'Box'
box_events_table = 'Events'

box_config = None
# Limit of Box events to retrieve before starting to paginate
limit = 100

# Previous stream position to use for events pagination
previous_stream_position = 0
month_lookback = 1
last_event_created_at = None
box_events = []


def insert_box_events():
    # Hyper file instantiation
    path_to_database = Path(box_hyper_file)
    hyper_file_exists = Path.exists(path_to_database)

    # Start the Hyper API pricess
    with HyperProcess(telemetry=Telemetry.SEND_USAGE_DATA_TO_TABLEAU) as hyper:

        # Check if the Hyper file exists or not. CreateMode.NONE will append. CreateMode.CREATE_AND_REPLACE will create a net new file
        create_mode = None
        if hyper_file_exists:
            create_mode = CreateMode.NONE
        else:
            create_mode = CreateMode.CREATE_AND_REPLACE

        # Open a new connection
        with Connection(endpoint=hyper.endpoint, database=path_to_database, create_mode=create_mode) as connection:
            # Check a new schema if it does not exist
            connection.catalog.create_schema_if_not_exists(schema=box_schema)

            # Instantiate the table schema
            box_events_table_def = TableDefinition(
                table_name=TableName(box_schema, box_events_table),
                columns=[
                    TableDefinition.Column(name='event_id', type=SqlType.text(), nullability=NULLABLE),
                    TableDefinition.Column(name='event_type', type=SqlType.text(), nullability=NULLABLE),
                    TableDefinition.Column(name='created_at', type=SqlType.timestamp_tz(), nullability=NULLABLE),
                    TableDefinition.Column(name='created_by_id', type=SqlType.text(), nullability=NULLABLE),
                    TableDefinition.Column(name='created_by_name', type=SqlType.text(), nullability=NULLABLE),
                    TableDefinition.Column(name='created_by_login', type=SqlType.text(), nullability=NULLABLE),
                    TableDefinition.Column(name='source', type=SqlType.json(), nullability=NULLABLE),
                    TableDefinition.Column(name='ip_address', type=SqlType.text(), nullability=NULLABLE),
                    TableDefinition.Column(name='additional_details', type=SqlType.json(), nullability=NULLABLE)
                ]
            )
            print('Found schema: {0} and table def: {1}'.format(box_events_table_def.table_name.schema_name, box_events_table_def.table_name))
            # Create the table if it does not exist and get the Box events table
            connection.catalog.create_table_if_not_exists(table_definition=box_events_table_def)
            table_name = TableName(box_schema, box_events_table)

            # Get the MAX row by created_at
            last_event_created_at = connection.execute_scalar_query(query=f"SELECT MAX(created_at) FROM {box_events_table_def.table_name}")
            if last_event_created_at is not None:
                print('Found last event in hyper file: {0}'.format(last_event_created_at.to_datetime()))

            # Get the Box service account client
            auth = JWTAuth.from_settings_file(box_config)
            box_client = Client(auth)
            service_account = box_client.user().get()
            print('Found Service Account with name: {0}, id: {1}, and login: {2}'.format(service_account.name, service_account.id, service_account.login))

            # Get the current date and the date for one month ago if there is not lastest event
            today = datetime.utcnow()
            if last_event_created_at is None:
                last_event_created_at = today - relativedelta.relativedelta(months=month_lookback)
            else:
                last_event_created_at = last_event_created_at.to_datetime().replace(tzinfo=timezone.utc).astimezone(tz=None)

            # Get the Box enterprise events for a given date range
            print('Using date range for events  today: {0} and starting datetime: {1}'.format(today, last_event_created_at))
            get_box_events(box_client, previous_stream_position, last_event_created_at, today)

            # Insert the Box enteprise events into the Hyper file
            with Inserter(connection, box_events_table_def) as inserter:
                inserter.add_rows(rows=box_events)
                inserter.execute()

            # Number of rows in the "Box"."Events" table.
            row_count = connection.execute_scalar_query(query=f"SELECT COUNT(*) FROM {table_name}")
            print(f"The number of rows in table {table_name} is {row_count}.")
        print("The connection to the Hyper file has been closed.")
    print("The Hyper process has been shut down.")

def get_box_events(box_client, stream_position, created_after, created_before):
    # Populate the URL query parameters
    url_params = 'stream_type=admin_logs&limit={0}&stream_position={1}&created_after={2}&created_before={3}'.format(limit, stream_position, created_after, created_before)

    # Set the previous stream position so we can compare it later on
    previous_stream_position = stream_position

    # GET request to retrieve events
    events_response = box_client.make_request(
        'GET',
        box_client.get_url('events?{0}'.format(url_params)),
    ).json()

    # Get the next stream position
    next_stream_position = events_response['next_stream_position']
    chunk_size = events_response['chunk_size']
    print('Found events response with chunk_size={0}, next_stream_position={1}, and previous_stream_position={2}'.format(chunk_size, next_stream_position, previous_stream_position))

    # Loop through the events and store them in a dictionary.
    events = events_response['entries']
    for event in events:
        event_data = []
        event_data.append(event['event_id'])
        event_data.append(event['event_type'])
        event_data.append(dateparser.parse(event['created_at']))
        event_data.append(event['created_by']['id'])
        event_data.append(event['created_by']['name'])
        event_data.append(event['created_by']['login'])
        event_data.append(json.dumps(event['source']))
        event_data.append(event['ip_address'])
        event_data.append(json.dumps(event['additional_details']))
        box_events.append(event_data)

    # If the previous stream position is not equal to the next stream position, we need to continue to paginate and call the function reflectively
    if previous_stream_position != next_stream_position:
        get_box_events(box_client, next_stream_position, created_after, created_before)

# Pass into commandline args
if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description='Create Tableau Hyper file from Box events.')
        parser.add_argument('--box_config', metavar='/path/to/my/box_config.json', required=True, help='The path to your Box JWT app config')
        args = parser.parse_args()
        box_config = args.box_config

        # Call the insert_box_events function
        insert_box_events()
    except HyperException as ex:
        print(ex)
        exit(1)

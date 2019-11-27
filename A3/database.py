import boto3
from botocore.exceptions import ClientError


########################################################################

#######       METHODS AVAILABLE   #######
#   create_account(company_name)
#   insert_into_<table_name>(company_name, other_fields_in_table)
#   delete_item(company_name, table_name, primary_key, primary_key_value)
#   get_item(company_name, table_name, primary_key, primary_key_value)
#
########################################################################

AWS_ACCESS_KEY_ID = 'AKIAIJK4UQ7KTGQZY4OQ'
AWS_SECRET_KEY = '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'

boto_session = boto3.Session(aws_access_key_id=AWS_ACCESS_KEY_ID,
                            aws_secret_access_key=AWS_SECRET_KEY,
                            region_name='us-east-1')

dynamodb = boto_session.resource('dynamodb')
dynamodb_client = boto_session.client('dynamodb')

#Helper
def get_table_name(company_name, table_name):
    return company_name + '_' + table_name

# Creates a table with given primary key and primary key type
def create_table(name, primary_key, primary_key_type):
    table = dynamodb.create_table(
        TableName=name,
        KeySchema=[
            {
                'AttributeName': primary_key,
                'KeyType': 'HASH'  #Partition key
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': primary_key,
                'AttributeType': primary_key_type
            },     
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        },
        Tags=[
            {
            'Key': 'TableName',
            'Value': name
            }
        ]
    )

    #Wait until table is created
    table.meta.client.get_waiter('table_exists').wait(TableName=name)
    print(table.item_count)
    print("Table status:", table.table_status)
    return


# Registers a new account and creates corresponding tables
def create_account(name):
    current_tables = dynamodb_client.list_tables()['TableNames']
    #runs the first time to create an Accounts table
    if 'Accounts' not in current_tables:
        create_table('Accounts', 'AccountName', 'S')

    #Insert new account details into Accounts table and create other tables
    account_data = {'AccountName': name}
    insert_into_table('Accounts', account_data)
    print('Added new account')
    print('Creating other tables')

    # USERS
    user_table_name = get_table_name(name, 'users')
    create_table(user_table_name, 'username', 'S')

    # APPLICATIONS
    app_table_name = get_table_name(name, 'applications')
    create_table(app_table_name, 'application_name', 'S')

    # NODES
    node_table_name = get_table_name(name, 'nodes')
    create_table(node_table_name, 'node_ID', 'N')

    # ALERTS
    alerts_table_name = get_table_name(name, 'alerts')
    create_table(alerts_table_name, 'alert_ID', 'N')

    # ACTION GROUP
    actionGroup_name = get_table_name(name, 'action_group')
    create_table(actionGroup_name, 'group_ID', 'N')

    # POLICY
    policy_table_name = get_table_name(name, 'policies')
    create_table(policy_table_name, 'policy_ID', 'N')

    # WIDGETS
    widget_table_name = get_table_name(name, 'widgets')
    create_table(widget_table_name, 'widget_ID', 'N')

    # DASHBOARD
    policy_table_name = get_table_name(name, 'dashboards')
    create_table(policy_table_name, 'dashboard_ID', 'N')

    print('Initialized tables for new account')


def insert_into_table(table_name, data): # (string, dict) -> None
    table = dynamodb.Table(table_name)
    '''
    test_key = 'test_key1'
    username = 'test_username1'
    password = 'test_password1'
    table.put_item(
        Item={ 
            'test_key': test_key,
            'username': username,
            'password': password
        }
    )
    '''
    table.put_item(
        Item=data
    )
    print("Successfully inserted data into {} table".format(table_name))
    return

# Returns dictionary of entire row as key value pairs
def get_item(company_name, table_name, primary_key, primary_key_value):
    table_name = get_table_name(company_name, table_name)
    table = dynamodb.Table(table_name)
    try:
        response = table.get_item(
            Key={
                primary_key: primary_key_value
            }
        )
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        item = response['Item']
        print('Successfully retrieved item')
        return item
    return


### Inserting in all the tables - uses insert_into_table
def insert_into_users(company_name, username, password, access):
    table_name = get_table_name(company_name, 'users')
    data = {
        'username': username,
        'password': password,
        'access': access
    }
    insert_into_table(table_name, data)

def insert_into_applications(company_name, application_name, file_):
    table_name = get_table_name(company_name, 'applications')
    data = {
        'application_name': application_name,
        'file': file_
    }
    insert_into_table(table_name, data)

def insert_into_nodes(company_name, node_ID, application_name):
    table_name = get_table_name(company_name, 'nodes')
    data = {
        'node_ID': node_ID,
        'application_name': application_name
    }
    insert_into_table(table_name, data)

def insert_into_alerts(company_name, alert_ID, node_ID, query):
    table_name = get_table_name(company_name, 'alerts')
    data = {
        'alert_ID': alert_ID,
        'node_ID': node_ID,
        'query': query
    }
    insert_into_table(table_name, data)
    
def insert_into_action_group(company_name, group_ID, action):
    table_name = get_table_name(company_name, 'action_group')
    data = {
        'group_ID': group_ID,
        'action': action
    }
    insert_into_table(table_name, data)

def insert_into_policies(company_name, policy_ID, group_ID, alerts):
    table_name = get_table_name(company_name, 'policies')
    data = {
        'policy_ID': policy_ID,
        'group_ID': group_ID,
        'alerts': alerts
    }
    insert_into_table(table_name, data)

def insert_into_widgets(company_name, widget_ID, dashboard_ID, query):
    table_name = get_table_name(company_name, 'widgets')
    data = {
        'widget_ID': widget_ID,
        'dashboard_ID': dashboard_ID,
        'query': query
    }
    insert_into_table(table_name, data)

def insert_into_dashboards(company_name, dashboard_ID):
    table_name = get_table_name(company_name, 'dashboards')
    data = {
        'dashboard_ID': dashboard_ID
    }
    insert_into_table(table_name, data)


# Delete item from table
def delete_item(company_name, table_name, primary_key, primary_key_value):
    table_name = get_table_name(company_name, table_name)
    table = dynamodb.Table(table_name)
    try:
        response = table.delete_item(
            Key={
                primary_key: primary_key_value
            }
        )
    except ClientError as e:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print(e.response['Error']['Message'])
    else:
        print("DeleteItem succeeded:")

# Accounts - AccountName
# Users - username, password, access
# Application - application ID, file
# Nodes - nodeID, application ID
# Alerts - ID, node, sql query
# Action Group - ID, action
# Policy - ID, Action group ID, Alerts
# Widgets - widget ID, dashboard, SQL query
# Dashboard - ID

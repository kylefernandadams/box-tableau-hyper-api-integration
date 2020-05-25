import argparse
import getpass
import tableauserverclient as TSC

box_datasource_name = 'Box Enterprise Events'

# Class to handle password commandline arg
class Password(argparse.Action):
     def __call__(self, parser, namespace, values, option_string=None):
         pwd = getpass.getpass()
         setattr(namespace, self.dest, pwd)

# Definition to publish a hyper file
def publish_hyper(server, site_id, project_name, hyper_file_path, username, password):

    # Instantiate the Tableau server and auth vars
    server = TSC.Server(server, use_server_version=True)
    auth = TSC.TableauAuth(username, password, site_id = site_id)

    # Sign into Tableau
    with server.auth.sign_in(auth):
        print('Logged into server: {0}, site_id: {1}, with username: {2}'.format(server.server_address, site_id, username))

        # Page through the different projects and try to find the matching project
        project_id = None
        for project in TSC.Pager(server.projects):
            if project.name == project_name:
                project_id = project.id
                print('Found matching project id: {0} and project_name: {1}'.format(project.id, project.name))
        
        # If we find a matching project name, publish the hyper file
        if project:
            print('Publishing hyper file: {0} to project name: {1}'.format(hyper_file_path, project_name))
            datasource = TSC.DatasourceItem(project_id, name=box_datasource_name)
            item = server.datasources.publish(datasource, hyper_file_path, 'Overwrite')
            print('Successfully published datasource: {0} with id: {1}'.format(item.name, item.id))
        else:
            print('No project with name: {0} found!'.format(project_name))

    # Sign out of the Tableau session
    server.auth.sign_out()

# Pass into commandline args
if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description='Publish Box Events Hyper file.')
        parser.add_argument('--server', metavar='https://10ax.online.tableau.com/', required=True, help='Tableau server URL')
        parser.add_argument('--site_id', metavar='my-site', required=True, help='Tableau Site ID')
        parser.add_argument('--project_name', metavar='Box', required=True, help='Tableau project name')
        parser.add_argument('--hyper_file_path', metavar='path/to/my/box_events.hyper', required=True, help='Tableau Hyper file path')
        parser.add_argument('--username', metavar='me@email.com', required=True, help='Tableau username')
        parser.add_argument('--password', metavar='secret', action=Password, required=True, help='Tableau password', nargs=0)
        args = parser.parse_args()

        # Call the publish_hyper function
        publish_hyper(args.server, args.site_id, args.project_name, args.hyper_file_path, args.username, args.password)
    except Exception as ex:
        print(ex)
        exit(1)
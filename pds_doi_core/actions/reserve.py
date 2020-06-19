import os


from pds_doi_core.actions.action import DOICoreAction
from pds_doi_core.input.exeptions import InputFormatException, UnknownNodeException
from pds_doi_core.util.general_util import get_logger

logger = get_logger('pds_doi_core.actions.reserve')


class DOICoreActionReserve(DOICoreAction):
    _name = 'reserve'
    description = ' % pds-doi-cmd reserve -c img -s Qui.T.Chau@jpl.nasa.gov -i input/DOI_Reserved_GEO_200318.csv\n'

    def __init__(self):
        super().__init__()

    @classmethod
    def add_to_subparser(cls, subparsers):
        action_parser = subparsers.add_parser(cls._name)
        action_parser.add_argument('-c', '--node-id',
                                   help='The pds discipline node in charge of the submission of the DOI',
                                   required=True,
                                   metavar='"img"')
        action_parser.add_argument('-i', '--input',
                                   help='A pds4 label local or on http, a xls spreadsheet, a database file'
                                        ' is also supported to reserve a list of doi',
                                   required=True,
                                   metavar='input/DOI_Reserved_GEO_200318.csv')
        action_parser.add_argument('-s', '--submitter-email',
                                   help='The email address of the user performing the action for these services',
                                   required=True,
                                   metavar='"my.email@node.gov"')
#        action_parser.add_argument('-t', '--target',
#                                   help='the system target to mint the DOI',
#                                   required=False,
#                                   default='osti',
#                                   metavar='osti')

    def _process_reserve_action_xlsx(self, target_url):
        '''Function process a reserve action based on .xlsx ending.'''

        doi_directory_pathname = os.path.join('.', 'output')
        os.makedirs(doi_directory_pathname, exist_ok=True)

        try:
            dict_condition_data = self.m_doi_input_util.parse_sxls_file(target_url)

            # Do a sanity check on content of dict_condition_data.
            if len(dict_condition_data) == 0:
                raise InputFormatException("Length of dict_condition_data['dois'] is zero, target_url " + target_url)

            return dict_condition_data
        except InputFormatException as e:
            logger.error(e)
            exit(1)

    def _process_reserve_action_csv(self, target_url):
        '''Function process a reserve action based on .csv ending.'''

        doi_directory_pathname = os.path.join('.', 'output')
        os.makedirs(doi_directory_pathname, exist_ok=True)

        try:
            dict_condition_data = self.m_doi_input_util.parse_csv_file(target_url)

            # Do a sanity check on content of dict_condition_data.
            if len(dict_condition_data) == 0:
                raise InputFormatException("Length of dict_condition_data['dois'] is zero, target_url " + target_url)

            return dict_condition_data
        except InputFormatException as e:
            logger.error(e)
            exit(1)

    def run(self,
            target_url,
            node_id,
            submitter_email,
            submit_label_flag=True):
        """
        Function receives a URI containing either XML, SXLS or CSV and create one or many labels to disk and submit these label(s) to OSTI.
        :param target_url:
        :param node_id:
        :param submitter_email:
        :return:
        """

        try:
            contributor_value = self.m_node_util.get_node_long_name(node_id)
        except UnknownNodeException as e:
            raise e

        action_type = 'reserve_osti_label'
        o_doi_label = 'invalid action type:action_type ' + action_type
        publisher_value = self._config.get('OTHER', 'doi_publisher')

        logger.debug(f"target_url,action_type {target_url} {action_type}")

        if target_url.endswith('.xml'):
            doi_fields = self.m_doi_pds4_label.parse_pds4_label_via_uri(target_url, publisher_value, contributor_value)
            o_doi_label = self.m_doi_output_osti.create_osti_doi_reserved_record(doi_fields)

        elif target_url.endswith('.xlsx'):
            doi_fields = self._process_reserve_action_xlsx(target_url)
            o_doi_label = self.m_doi_output_osti.create_osti_doi_reserved_record(doi_fields)

        elif target_url.endswith('.csv'):
            doi_fields = self._process_reserve_action_csv(target_url)
            o_doi_label = self.m_doi_output_osti.create_osti_doi_reserved_record(doi_fields)

        # Check to see if the given file has an attempt to process.
        else:
            logger.error(f"File type has not been implemented:target_url {target_url}")
            exit(1)

        logger.debug(f"submit_label_flag {submit_label_flag}")
        logger.debug(f"doi_fields {doi_fields} {type(doi_fields)}")
        logger.debug(f"o_doi_label {o_doi_label}")
        logger.debug(f"submitter_email {submitter_email}")

        # We can submit the content to OSTI if we wish.
        if submit_label_flag:
            from pds_doi_core.outputs.osti_web_client import DOIOstiWebClient
            doi_web_client = DOIOstiWebClient()
            response, output_str = doi_web_client.webclient_submit_existing_content(
                o_doi_label,
                i_url=self._config.get('OSTI', 'url'),
                i_username=self._config.get('OSTI', 'user'),
                i_password=self._config.get('OSTI', 'password'))

            for doi_field in doi_fields:
                doi_field['status'] = response[doi_field['related_identifier']]['status'].lower()
                doi_field['doi'] = response[doi_field['related_identifier']]['doi']

            logger.debug(f"reserve_response {output_str}")
            logger.debug(f"type(reserve_response) {type(output_str)}")

            # Use the service of TransactionBuilder to prepare all things related to writing a transaction.
            transaction_obj = self.m_transaction_builder.prepare_transaction(target_url,
                                                                             node_id,
                                                                             submitter_email,
                                                                             doi_fields,
                                                                             output_content=output_str)
            # Write a transaction for the 'reserve' action.
            transaction_obj.log()

            return output_str
        else:
            # This path is normally used by developer to test the parsing of CSV or XLSX input without submitting the DOI.
            # Write a transaction for the 'reserve' action.
            for doi_field in doi_fields:
                doi_field['status'] = 'reserved_not_submitted'
            # Use the service of TransactionBuilder to prepare all things related to writing a transaction.
            transaction_obj = self.m_transaction_builder.prepare_transaction(target_url,
                                                                             node_id,
                                                                             submitter_email,
                                                                             doi_fields,
                                                                             output_content=o_doi_label)

            # Write a transaction for the 'reserve' action.
            transaction_obj.log()

            return o_doi_label

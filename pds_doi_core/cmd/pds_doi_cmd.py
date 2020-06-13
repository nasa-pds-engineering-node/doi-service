#!/bin/python
#
#  Copyright 2020, by the California Institute of Technology.  ALL RIGHTS
#  RESERVED. United States Government Sponsorship acknowledged. Any commercial
#  use must be negotiated with the Office of Technology Transfer at the
#  California Institute of Technology.
#
# ------------------------------
import os

from pds_doi_core.util.cmd_parser import create_cmd_parser
from pds_doi_core.util.general_util import get_logger
from pds_doi_core.input.exeptions import UnknownNodeException
from pds_doi_core.actions.reserve import DOICoreActionReserve
from pds_doi_core.actions.draft import DOICoreActionDraft

# Get the common logger and set the level for this file.
logger = get_logger('pds_doi_core.cmd.pds_doi_cmd')


def main():
    parser = create_cmd_parser()
    arguments = parser.parse_args()
    action_type = arguments.action
    submitter_email = arguments.submitter_email
    node_id = arguments.node_id.lstrip().rstrip()  # Remove any leading and trailing blanks.
    input_location = arguments.input

    logger.info(f"run_dir {os.getcwd()}")
    logger.info(f"input_location {input_location}")
    logger.info(f"node_id ['{node_id}']")

    try:
        if action_type == 'draft':
            draft = DOICoreActionDraft()
            o_doi_label = draft.run(input_location, node_id, submitter_email)
            logger.info(o_doi_label)

        elif action_type == 'reserve':
            reserve = DOICoreActionReserve()
            o_doi_label = reserve.run(input_location,
                                      node_id,
                                      submitter_email,
                                      submit_label_flag=True)
            # By default, submit_label_flag=True if not specified.
            # By default, write_to_file_flag=True if not specified.
            logger.info(o_doi_label)
        else:
            logger.error(f"Action {action_type} is not supported yet.")
            exit(1)
    except UnknownNodeException as e:
        logger.error(e)
        exit(1)


if __name__ == '__main__':
    main()

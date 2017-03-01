import getpass

from boto.exception import S3ResponseError
from dmapiclient import APIError
from dmutils.documents import generate_timestamped_document_upload_path, generate_download_filename, \
    COUNTERPART_FILENAME

from dmscripts.bulk_upload_documents import get_supplier_id_from_framework_file_path
from dmscripts.helpers import logging_helpers
from dmscripts.helpers.logging_helpers import logging

logger = logging_helpers.configure_logger({'dmapiclient.base': logging.WARNING})


def upload_counterpart_file(bucket, framework_slug, file_path, dry_run, client):
    supplier_id = get_supplier_id_from_framework_file_path(file_path)
    supplier_framework = client.get_supplier_framework_info(supplier_id, framework_slug)
    supplier_framework = supplier_framework['frameworkInterest']
    supplier_name = supplier_framework['declaration']['nameOfOrganisation']
    download_filename = generate_download_filename(supplier_id, COUNTERPART_FILENAME, supplier_name)

    upload_path = generate_timestamped_document_upload_path(
        framework_slug,
        supplier_id,
        "agreements",
        COUNTERPART_FILENAME
    )
    try:
        if not dry_run:
            # Upload file
            with open(file_path) as source_file:
                bucket.save(upload_path, source_file, acl='private', move_prefix=None,
                            download_filename=download_filename)
                logger.info("UPLOADED: '{}' to '{}'".format(file_path, upload_path))

            # Save filepath to framework agreement
            client.update_framework_agreement(
                supplier_framework['agreementId'],
                {"countersignedAgreementPath": upload_path},
                'upload-counterpart-agreements script run by {}'.format(getpass.getuser())
            )
            logger.info("countersignedAgreementPath='{}' for agreement ID {}".format(
                upload_path, supplier_framework['agreementId'])
            )
        else:
            logger.info("[Dry-run] UPLOAD: '{}' to '{}'".format(file_path, upload_path))
            logger.info("[Dry-run] countersignedAgreementPath='{}' for agreement ID {}".format(
                upload_path, supplier_framework['agreementId'])
            )
    except (OSError, IOError) as e:
        logger.error("Error reading file '{}': {}".format(file_path, e.message))
    except S3ResponseError as e:
        logger.error("Error uploading '{}' to '{}': {}".format(file_path, upload_path, e.message))
    except APIError as e:
        logger.error("API error setting upload path '{}' on agreement ID {}: {}".format(
            upload_path,
            supplier_framework['agreementId'],
            e.message)
        )

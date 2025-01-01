import os
import requests
from azure.storage.blob import BlobServiceClient
import logging
import json
from django.conf import settings
from sync_data.models import ParamSynchro,SyncLog,SyncStatus

logger = logging.getLogger(__name__)


class AuthenticationRfeService:
    def __init__(self):
        self.api_url = settings.API_URL
    def get_token_bearer(self, project_access):
        try:
            token_endpoint = f"https://retail-services.cegid.cloud/{project_access.environment}/as/connect/token"

            data = {
                'client_id': 'CegidRetailResourceFlowClient',
                'username': f"{project_access.username}@{project_access.workspace}",
                'password': project_access.password,
                'grant_type': 'password',
                'scope': 'RetailBackendApi offline_access'
            }

            print(f"Requesting token from: {token_endpoint}")
            print(f"With data: {json.dumps(data, indent=2)}")

            response = requests.post(token_endpoint, data=data)

            print(f"Token response status: {response.status_code}")
            print(f"Token response: {response.text}")

            if response.status_code == 200:
                return response.json()['access_token']
            return None

        except Exception as e:
            print(f"Error getting token: {str(e)}")
            return None

    def get_azure_storage_config(self, project_access):
        try:
            token_bearer = self.get_token_bearer(project_access)
            if not token_bearer:
                print("Failed to get token bearer")
                return None

            api_url = (
                f"https://rfe.cegid.cloud/{project_access.environment}/storage/api/"
                f"{project_access.workspace}/RFE/V1/getsastoken/{project_access.container_name}"
                "?Minutes-To-Live=3000"
            )

            headers = {
                'Authorization': f'Bearer {token_bearer}',
                'Accept': 'application/json'
            }

            print(f"Requesting Azure config from: {api_url}")
            print(f"With headers: {json.dumps(headers, indent=2)}")

            response = requests.get(api_url, headers=headers)

            print(f"Config response status: {response.status_code}")
            print(f"Config response: {response.text}")

            if response.status_code == 200:
                return response.json()
            return None

        except Exception as e:
            print(f"Error getting Azure config: {str(e)}")
            return None

    def upload_to_api(self, file_path: str,api_spec: str) -> bool:
        try:
            # Prepare the file for upload
            with open(file_path, 'rb') as file:
                files = {'file': file}
                response = requests.post(
                    f"{self.api_url}/{api_spec}/page=1",
                    files=files
                )

            if response.status_code == 200:
                logger.info(f"Successfully uploaded and processed file {file_path}")
                return True
            else:
                logger.error(
                    f"Failed to upload file {file_path}. Status: {response.status_code}, Response: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Exception uploading file to articles API: {str(e)}")
            return False

    def download_files_from_folder(self, project_access, destination_path,api_spec):
        success = SyncStatus()
        try:
            print("Starting download process...")
            azure_storage_config = self.get_azure_storage_config(project_access)

            if not azure_storage_config:
                print("Azure Storage Configuration is null")
                success.status = False
                success.log = SyncLog(
                    file_name='',
                    status='FAILED',
                    error_message='Azure Storage Configuration is null'
                )
                return success

            print(f"Got storage config: {json.dumps(azure_storage_config, indent=2)}")

            blob_service_client = BlobServiceClient(
                f"{azure_storage_config['blobServiceUri']}{azure_storage_config['sasToken']}"
            )

            container_client = blob_service_client.get_container_client(
                azure_storage_config['containerName']
            )

            os.makedirs(destination_path, exist_ok=True)

            # List all blobs in the directory
            blob_list = container_client.list_blobs(name_starts_with=project_access.path)
            csv_blobs = [blob for blob in blob_list if blob.name.endswith('.csv')]
            if not csv_blobs:
                print("No CSV files found")
                success.status = False
                success.log = SyncLog(
                    file_name='',
                    status='FAILED',
                    error_message='No CSV files found'
                )
                return success

            for blob in csv_blobs:
                try:
                    blob_client = container_client.get_blob_client(blob.name)
                    local_file_path = os.path.join(
                        destination_path,
                        os.path.basename(blob.name)
                    )

                    print(f"Downloading {blob.name} to {local_file_path}")

                    with open(local_file_path, "wb") as file:
                        download_stream = blob_client.download_blob()
                        file.write(download_stream.readall())

                    api_upload_success = self.upload_to_api(local_file_path,api_spec)

                    if api_upload_success:
                        new_blob_client = container_client.get_blob_client(f"{blob.name}.ar")
                        new_blob_client.start_copy_from_url(blob_client.url)
                        blob_client.delete_blob()
                        success.status=True
                        success.log=SyncLog(
                            file_name=blob.name,
                            status='SUCCESS'
                        )
                    else:
                        success.log = SyncLog(
                            file_name=blob.name,
                            status='API_UPLOAD_FAILED',
                            error_message='Failed to upload to API'
                        )
                        success.status = False

                except Exception as e:
                    print(f"Error processing file {blob.name}: {str(e)}")
                    success.log = SyncLog(
                        file_name=blob.name,
                        status='FAILED',
                        error_message=str(e)
                    )
                    success.status = False

            return success

        except Exception as e:
            print(f"Error in download process: {str(e)}")
            success.log = SyncLog(
                file_name=project_access.path,
                status='FAILED',
                error_message=str(e)
            )
            success.status = False
            return success
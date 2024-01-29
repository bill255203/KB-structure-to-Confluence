# Google Drive Knowledge Base to Confluence Integration

## **Project Overview**

This project facilitates the synchronization of hierarchical structures and associated links from Google Drive to Confluence by coordinating Cloud Scheduler, Cloud Pub/Sub, Cloud Functions, and Cloud Storage.

- **Workflow Diagram:** This visual diagram shows the sequence and interaction of components involved in the migration process.

![alt text](img.png)

# **How to Use**

## **Prerequisites Settings**

1. **Setting Up Authorization**

   (a) **Service Account Authorization**: Create a service account with **`roles/cloudfunctions.invoker`** and **`roles/storage.objectViewer`** roles for your Google Cloud Platform (GCP) project and add the email, e.g., **`bill-105@tw-rd-de-bill-404606.iam.gserviceaccount.com`**, to the authorized list for the target Google Drive folder. This step grants necessary access permissions to the service account for the specific Google Drive folder.

   (b) **Service Account File**: Download the Service account file . Rename this file to **`client_secret.json`**. This file serves as a key to authorize our system to access and manage specific Google Cloud functions and storage.

   (Result): Service account has been successfully authorized for the target Google Drive folder and has the ability to invoke cloud functions and has access to your cloud storage, also `client_secret.json` has been obtained for authorization.

2. **Configure Access to Confluence**

   (a) **API Token**: Obtain an API token from your Atlassian account by visiting Atlassian API Token Management. This token allows our system to securely access and manage your Confluence pages.(https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)

   (b) **Update Configuration File**: In the **`confluence_secret.json`** file, replace `API_TOKEN` and `EMAIL` with your token and email. This configures the system to authenticate with Confluence using your credentials.

   (Result): Successfully obtained API token and configured `confluence_secret.json` with authentication credentials.

## **Preparing for Structure Replication**

1. **Identify Confluence Page and Space IDs**

   (a) **Finding page ID**: Locate the parent ID for your Confluence page: Open the `Main Page` of your Confluence board > **`More Actions`** > **`Page Information`**. The parent_id is in the URL.

   (b) **Finding space ID**: Using **`spaceid.py`** in the root folder by replacing the `url=https://cloudmile4service.atlassian.net/wiki/api/v2/pages/<PARENT_ID>` with your parent_id and fill in the **`API_TOKEN`** with yours. Run the script to get the spaceID of your page.

   (c) **Update Configuration File**: In the **`confluence_secret.json`** file, replace `SPACE_ID` and `PARENT_ID`. This configuration helps Confluence identify the specific location or page where you intend to make updates.

   (Result): Successfully identified and configured Confluence Page and Space IDs.

2. **Setting Up Cloud Storage**

   (a) **Create Storage Bucket**: Create a bucket named **`kb-confluence`** in Google Cloud. This bucket will store necessary files for the migration.

   (b) **Uploading Files**: Upload **`created_pages.json`**, **`prefix_titles.json`**, **`client_secret.json`**, and **`confluence_secret.json`** to this bucket. These files are crucial for the migration process.

   (Result): Cloud Storage bucket created, and required files uploaded.

## **Automating the Structure Replication Process**

1. **Cloud Function, Cloud Pub/Sub and Cloud Scheduler Setup**:

   (a) Create a new cloud function named `kb-function`. For the trigger, choose the type `cloud pub/sub` and create a new topic named `kb-pub`. Set the runtime settings, including a timeout value of `600 seconds`, due to the lengthy nature of the process. Click next to proceed.

   (b) In the function configuration, set the programming language to `Python 3.11`. Specify `main` as the entry point for the function. This is where the cloud function begins execution. Then, copy the `requirements.txt` file and the `main.py` script. These files contain the necessary dependencies and the main logic for the migration function. Click `deploy` to finalize the setup of your cloud function.

   (c) Create a new cloud scheduler with a cron frequency of `0 0 1 * *`, meaning the process will execute automatically once every month. Set the target type to `pub/sub` and select the `kb-pub` topic that you previously created. This scheduler acts as an automated trigger for the cloud function, initiating the migration process on a regular schedule.

   (Result): Cloud function, pub/sub topic, and scheduler set up for automated structure replication process.

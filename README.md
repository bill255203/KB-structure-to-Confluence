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

   (b) **Uploading Files**: Upload **`created_pages.json`** and **`prefix_titles.json`** located in the project root folder aiming to record the name of created pages to avoid duplicate names. Also, upload **`client_secret.json`** and **`confluence_secret.json`** to this bucket. These files are crucial for the authentication of the replication process.

   (Result): Cloud Storage bucket created, and required files uploaded.

## **Automating the Structure Replication Process**

1. **Cloud Function, Cloud Pub/Sub and Cloud Scheduler Setup**:

   (a) Create a new cloud function named `kb-function`. For the trigger, choose the type `cloud pub/sub` and click `create a new topic` and name it `kb-pub`, click `create`. In the next section of execution phase, set timeout value of `540 seconds` due to the lengthy nature of the process. Click `next` to proceed.

   (b) In the function configuration, set the programming language on the top left corner to `Python 3.11` and specify the entry point as `main`, this is where the cloud function begins execution. Then, copy the `main.py` and `requirements.txt` script provided to the function. These files contain the necessary dependencies and the main logic for the function. Click `deploy` to finalize the setup of your cloud function.

   (c) Create a new cloud scheduler named `kb-scheduler` with a cron frequency of `0 0 1 * *`, meaning the process will execute automatically once every month, click `continue`. Set the target type to `pub/sub` and select the `kb-pub` topic that you previously created, click `create`. This scheduler acts as an automated trigger for the cloud function, initiating the migration process on a regular schedule.

   (Result): Cloud function, pub/sub topic, and scheduler set up for automated structure replication process.

## **Debugging the Process**

To debug the process, follow these steps carefully:

### **1. View Cloud Function Logs**

Go to Google Cloud Platform (GCP) and access the Cloud Functions section. Find the **`kb-function`** and click on it. Then, click on the "Record" option to view the log records during the function's execution.

### **2. Check for Initialization**

At the beginning of the execution, ensure that you see the following log message:

```
Init Pages: {}

```

If this message does not appear for the first time, it may indicate potential issues:

- The Cloud Storage might not be named correctly.
- There could be authorization problems.

### **3. Verify Google Drive Folder**

Check if the Google Drive folder is accessible. If you don't see the following log message:

```
Folder ID 0AJEo31zRZZG7Uk9PVA is a Google Drive Folder called: KB
Building folder structure for KB

```

It may indicate the following issues:

- The Google Service Account file may not have the necessary read access to the Google Drive folder.
- Permissions for executing the Cloud Function may not be correctly configured.
- The read access list is not added in the Google Drive folder.

### **4. Confluence Auth File**

If you encounter error messages like the following when creating pages:

```json
{
  "errors": [
    {
      "code": "NOT_FOUND",
      "detail": null,
      "status": 404,
      "title": "Not Found"
    }
  ]
}
```

It may suggest that the Confluence authentication file has incorrect settings. Review the authentication file to ensure it's properly configured.
The correct log messages should look something like this:

```json
{
  "_links": {
    "editui": "/pages/resumedraft.action?draftId=2083061852",
    "tinyui": "/x/XAApf",
    "webui": "/spaces/b/pages/2083061852/bill1"
  },
  "authorId": "712020:e6872501-a7b4-4126-905a-a57113e2c8af",
  "body": {
    "storage": {
      "representation": "storage",
      "value": "<a href=\"https://drive.google.com/drive/u/0/folders/0ANbyjco9413kUk9PVA\"> KB here</a>"
    }
  },
  "createdAt": "2024-01-26T08:10:17.341Z",
  "id": "2083061852",
  "lastOwnerId": null,
  "ownerId": null,
  "parentId": "2044466099"
}
```

Ensure that the log messages align with your expectations, indicating that the process is running as intended.

# from azureml.core import Workspace, Dataset, Datastore

# # Azure ML workspace details
# subscription_id = '485363cd-687d-4adb-a30b-35108c11d682'
# resource_group = 'medbot'
# workspace_name = 'karthik'

# # Connect to the Azure ML workspace
# workspace = Workspace(subscription_id, resource_group, workspace_name)

# # Access the datastore
# datastore = Datastore.get(workspace, "workspaceartifactstore")

# # Access the dataset
# dataset = Dataset.File.from_files(path=(datastore, 'converted_document_reference'))

# # Download the dataset to the current directory
# dataset.download(target_path='.', overwrite=True)

# print("Download completed successfully.")



from azureml.core import Workspace, Dataset, Datastore

subscription_id = '485363cd-687d-4adb-a30b-35108c11d682'
resource_group = 'medbot'
workspace_name = 'karthik'

workspace = Workspace(subscription_id, resource_group, workspace_name)

datastore = Datastore.get(workspace, "workspaceartifactstore")
dataset = Dataset.File.from_files(path=(datastore, 'converted_docs_json'))
dataset.download(target_path='/home/kap2403/Desktop/Medico-AI-Bot/dataset/converted_json_docs', overwrite=True)

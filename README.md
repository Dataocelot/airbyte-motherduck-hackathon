# Data-Driven Customer Support: Transforming the Customer supoport experience at 'Ocelot Living'

Ocelot Living is a brand that sells top home electronics to customers both online and in-store.

Recently, we discovered that a significant portion of customer support time is spent addressing repetitive queries that are already explained in the user manuals of our products. This not only overwhelms our Customer support team but also delays resolutions for more complex issues, impacting customer satisfaction.

In this hackathon, we aim to address this challenge by leveraging data and AI to create a scalable solution. Our mission is to enhance customer support efficiency while empowering customers to independently troubleshoot and resolve common issues.

## The Solution: `👷🏽‍♀️ Anuja`

We developed Anuja, a data-driven customer support chatbot designed to assist customers in resolving issues quickly and independently. By parsing product user manuals into actionable data, Anuja provides instant and accurate troubleshooting solutions. This allows our support team to focus on high-priority issues, improving overall service quality and customer experience.

<img src="docs/images/diagram-export-15-01-2025-01_28_11.png">

# Setting Up

## Requirements

For this project you will need to fill in the values of the following credentials found in the `test.env` and in `iac/dev.tfvars` files in the project root directory:

```bash
# Fill in your keys here
GEMINI_API_KEY= #Your Google GEMINI API key
BUCKET_NAME= #Your S3 Bucket name
DB_NAME= #Your DB name in Motherduck
AIRTABLE_API_KEY= #Your Airtable access token
ENVIRONMENT=AWS #Default is AWS or it can be LOCAL
AIRTABLE_BASE_ID= #The Airtable Base id
AIRTABLE_CUSTOMER_ACCOUNTS_TABLE_ID= #The Airtable Customer accounts table id
AIRBYTE_PRODUCT_TABLE_ID= #Your Airtable Product table id
AIRBYTE_WORKSPACE_ID= #Your Airtable workspace ID
AWS_ACCESS_KEY_ID= #Your AWS Access Key
AWS_SECRET_ACCESS_KEY= #Your AWS Secret Access Key
AIRBYTE_CLIENT_ID= # Your Airbyte application client ID
AIRBYTE_CLIENT_SECRET= # Your Airbyte application client secret
MOTHERDUCK_API_KEY= #Your Motherduck API key
```

```bash
airbyte_workspace_id  = "<FILL-IN>"
aws_access_key_id     = "<FILL-IN>"
aws_secret_access_key = "<FILL-IN>"
client_id             = "<FILL-IN>"
client_secret         = "<FILL-IN>"
motherduck_api_key    = "<FILL-IN>"
```

The `test.env` and the `dev.tfvars` files have the required keys for this project.

You will create an Airbyte cloud account, and you can sign up [here](https://airbyte.com/product/airbyte-cloud)
For your Gemini API key, you can sign up for Google Gemini, and access your API key [here](https://aistudio.google.com/apikey)
You must have a Motherduck account to access the Motherduck API key. [Here](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/authenticating-to-motherduck/#authentication-using-an-access-token) is the link that shows you how to get a Mother duck API key

After filling the values in the `test.env` file, you will need to rename the `tets.env` file to `.env`.

To get the project up and running, please make sure you have terraform set up on your machine, you can do install it from [here](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli) as we use Terraform to provision the resources needed for this project (AWS S3, Airbyte source, Docker container).

Assuming you have set up Terraform, and filled in your .env file, you can then run the following commands from the project root directory.

```bash
source .env
```

Next we create the resources by first changing the directory to the `iac` and then running the terraform commands. Terraform will create the required resources needed for the project.

```bash
cd iac
terraform init
terraform plan
terraform apply
```

## Airtable

[Here](https://airtable.com/app9prJZjrqpUAnZt/shrbOzAfiZVwzwO9D) is the CRM that was used for this project which was created, it was created in Airtable that . You can copy the base to your own airtable account workspace.

## Tools Used

- Airbyte: Data Ingestion
- MotherDuck: Data Warehouse
- Google Gemini: LLM
- Streamlit: User Interface
- Github Copilot: Code review
- Github: Version Control
- PyMuPDF: PDF parser
- AWS S3: Data lake
- Airtable: CRM
- Terraform: Infrastructure as code

# Data-Driven Customer Support: Transforming the Customer supoport experience at 'Ocelot Living'

Ocelot Living is a brand that sells top home electronics to customers both online and in-store.

Recently, we discovered that a significant portion of customer support time is spent addressing repetitive queries that are already explained in the user manuals of our products. This not only overwhelms our Customer support team but also delays resolutions for more complex issues, impacting customer satisfaction.

In this hackathon, we aim to address this challenge by leveraging data and AI to create a scalable solution. Our mission is to enhance customer support efficiency while empowering customers to independently troubleshoot and resolve common issues.

## The Solution: `👷🏽‍♀️ Anuja`

We developed Anuja, a data-driven customer support chatbot designed to assist customers in resolving issues quickly and independently. By parsing product user manuals into actionable data, Anuja provides instant and accurate troubleshooting solutions. This allows our support team to focus on high-priority issues, improving overall service quality and customer experience.

(Note: for this hackathon we limited the scope to only Dishwashers, but this can be extended to other applainces as well)

### Data Architecture

<img src="docs/images/diagram-export-15-01-2025-01_39_09.png">

#### 1. Data sources

The Data sources are as follows:

- A Airtable CRM made thst records appliances purchased by customers
  <img src="docs/images/customer_crm.png" alt="Airtable CRM table">

- An S3 bucket that conatins parsed PDFs saved as JSON files

# Setting Up

## Requirements

This project requires the following software installed:

- [Terraform](!https://developer.hashicorp.com/terraform/install) (for provisioning resources)
- [Docker desktop](!https://docs.docker.com/get-started/get-docker/) (for running the web app)

### Accounts

You will also need access to an [**Airbyte cloud account**](https://airbyte.com/product/airbyte-cloud), [**AWS account**](https://aws.amazon.com/), an [**Airtable account**](https://airtable.com), and [**Google Gemini**](https://gemini.google.com/) account

### Airtable

For Airtable, [here](https://airtable.com/app9prJZjrqpUAnZt/shrbOzAfiZVwzwO9D) is the CRM table that was used for this project. You can copy this base to your own airtable account workspace.

### Environmental variables

To set up Terraform and to successfully build the Docker image for this project you will need to fill in the values for the following credentials found in the [test.env](test.env) and in [iac/dev.tfvars](iac/dev.tfvars) files in the project's directory:

You can access your Airbyte `AIRBYTE_CLIENT_SECRET` and `AIRBYTE_CLIENT_ID` by following the steps included in this [link](!https://reference.airbyte.com/reference/authentication).

For your Google Gemini API key, you can sign up for Google Gemini, and access your `GEMINI_API_KEY` by following the steps [here](https://aistudio.google.com/apikey)

For your AWS keys, see this [link](!https://repost.aws/knowledge-center/create-access-key)

To get your Motherduck API key follow the steps [here](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/authenticating-to-motherduck/#authentication-using-an-access-token)

> [test.env](test.env)

```bash
# Fill in your keys here
GEMINI_API_KEY= #Your Google GEMINI API key
BUCKET_NAME= #Your S3 Bucket name
DB_NAME=my_db
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

> [iac/dev.tfvars](iac/dev.tfvars)

```bash
airbyte_workspace_id  = "<FILL-IN>"
aws_access_key_id     = "<FILL-IN>"
aws_secret_access_key = "<FILL-IN>"
client_id             = "<FILL-IN>"
client_secret         = "<FILL-IN>"
motherduck_api_key    = "<FILL-IN>"
```

## Steps

**Note**: After filling in the values for the `test.env` file, you will need to **rename the `test.env` file to `.env`**.

Assuming you have set up Terraform, and now have your .env file and your [iac/dev.tfvars](iac/dev.tfvars) filled in, you can then run the following commands from the project root directory.

```bash
source .env
```

Next, you can runn the following terraform commands and Terraform will create the required resources needed for the project.

```bash
cd iac
terraform init
terraform plan
terraform apply
```

If successful you should now see an s3 bucket already created, in s3 for you

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

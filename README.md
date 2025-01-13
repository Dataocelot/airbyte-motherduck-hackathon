# Data-Driven Customer Support: Transforming the Customer supoport experience at 'Appliance Ocelot'

Appliance Ocelot is a brand that sells top home electronics to customers both online and in-store.

Recently, we discovered that a significant portion of customer support time is spent addressing repetitive queries that are already explained in the user manuals of our products. This not only overwhelms our Customer support team but also delays resolutions for more complex issues, impacting customer satisfaction.

In this hackathon, we aim to address this challenge by leveraging data and AI to create a scalable solution. Our mission is to enhance customer support efficiency while empowering customers to independently troubleshoot and resolve common issues.

## The Solution: `Anuja`

We developed Anuja, a data-driven customer support chatbot designed to assist customers in resolving issues quickly and independently. By parsing product user manuals into actionable data, Anuja provides instant and accurate troubleshooting solutions. This allows our support team to focus on high-priority issues, improving overall service quality and customer experience.

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

## Requirements

For this project you will to fill in the values of the following credentials in order to test it locally:

```bash
# Fill in your keys here
GEMINI_API_KEY= #Your Google GEMINI API key
MOTHERDUCK_API_KEY= #Your Motherduck API key
BUCKET_NAME= #Your S3 Bucket name
DB_NAME= #Your DB name in Motherduck
AIRTABLE_ACCESS_TOKEN= #Your Airtable access token
ENVIRONMENT=LOCAL #Default is LOCAL or it can be AWS
AIRTABLE_BASE= #Your Airtable Base
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

The `test.env` file has the keys that are required for this project

You will to create an Airbyte cloud account, and you can sign up [here](https://airbyte.com/product/airbyte-cloud)
For your Gemini API key, you can sign up for Google Gemini, and access your API key [here](https://aistudio.google.com/apikey)
For Motherduck API key, you will need to have a Motherduck account. [Here](https://motherduck.com/docs/key-tasks/authenticating-and-connecting-to-motherduck/authenticating-to-motherduck/#authentication-using-an-access-token) is the link that shows you how to get a Motherduck API key

After filling the values the test.env file, you will need to rename it to a `.env`s

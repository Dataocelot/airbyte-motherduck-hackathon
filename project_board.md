# v0.0.1

## Project Board

### Done

- Create functionality to extract Table of contents from PDF [@cornzyblack]
- Restructure respective folders for parsed mardkown and images [@cornzyblack]

#### In progress

- Create PdfParser logic for extracting Troubleshooting section [@cornzyblack]
- Create UI for uploading files User manuals to S3 using Streamlit (admin portal) [@wayasay]
- Load parsed data on S3 into data models on Motherduck using airbyte cloud [@cornzyblack]

#### Bugs

- Make scanning table of contents by image with Gemini also work for more than 1 page TOC [@cornzyblack]
- Fix issue with too many log files getting created [@cornzyblack]

#### Todo

- Use Gemini to start answering questions based on Parsed text [@cornzyblack]
- Create UI for asking questions [@wayasay]
- Create Data model for Manual sections [@wayasay]
- Create Data model for TOC section [@wayasay]

#### Backlog

- Finetune a Gemini model to improve performance [@cornzyblack]
- Implement vector search in Mother duck [@cornzyblack]
- Load parsed data into data models on Motherduck using airbyte OSS [@cornzyblack]
- Load parsed data into S3 [@cornzyblack]
- Write + Add python tests [@cornzyblack]
- Setup Github actions CI/CD for python tests [@wayasay]
- Automatically set up

#### Enhancement

- Use SQLMesh for building data models
- Add supplementary information on Guides from ifixit
- Run quality checks on extracted data to ensure that they have relevant sections
- Build quality dashboards in SQLMesh
- Scanning Table of content by image with Tesseract not yet done
- Scanning Table of content by image with PYUMDF not yet done
- Deploy pdfprocessor to Lambda [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html) (Docker)
- Deploy infrastructure with Terraform

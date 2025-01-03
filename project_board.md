# v0.0.1

## Project Board

### Done

- Create functionality to extract Table of contents from PDF
- Restructure respective folders for parsed mardkown and images

#### In progress

#### Bugs

- Make scanning table of contents by image with Gemini also work for more than 1 page TOC
- Fix issue with too many log files getting created

#### Todo

- Create PdfParser logic for extracting Troubleshooting section [local]
- Create Data model for Troubleshooting section [local]
- Create Data model for TOC section [local]
- Create UI for uploading files [manuals] locally (admin portal) [local]
- Use Gemini to start answering questions based on Parsed text [local]
- Create UI for asking questions [local]

#### Backlog

- Create functionality to upload file from UI to S3
- Finetune a Gemini model to improve performance [local]
- Implement vector search in Mother duck [local]
- Load parsed data into data models on Motherduck using airbyte OSS [local]
- Load parsed data into S3
- Load parsed data on S3 into data models on Motherduck using airbyte cloud [preprod]
- Add python tests [local]
- Setup Github actions CI/CD for python tests [local]

#### Enhancement

- Use SQLMesh for building data models
- Add supplementary information on Guides from ifixit
- Run quality checks on extracted data to ensure that they have relevant sections
- Build quality dashboards in SQLMesh
- Scanning Table of content by image with Tesseract not yet done
- Scanning Table of content by image with PYUMDF not yet done
- Deploy pdfprocessor to Lambda [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html) (Docker)
-

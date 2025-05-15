# for lambda function
FROM public.ecr.aws/lambda/python:3.10

# Copy application code
COPY . ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Mangum to bridge FastAPI with AWS Lambda
RUN pip install mangum

CMD ["lambda_function.handler"]

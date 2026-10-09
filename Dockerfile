# AWS Lambda container image; includes OS libraries needed by WeasyPrint.
FROM public.ecr.aws/lambda/python:3.12

# WeasyPrint uses native text/layout libraries. Keep these in the same image as Python.
RUN dnf install -y \
      pango \
      cairo \
      libffi \
      gdk-pixbuf2 \
      shared-mime-info \
      dejavu-sans-fonts \
    && dnf clean all

COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY renderer.py lambda_handler.py ${LAMBDA_TASK_ROOT}/
COPY templates ${LAMBDA_TASK_ROOT}/templates
COPY static ${LAMBDA_TASK_ROOT}/static

CMD ["lambda_handler.handler"]

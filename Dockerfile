# syntax=docker/dockerfile:1

FROM jupyter/minimal-notebook:python-3.10

# install packages
# from requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /home/jovyan/work

EXPOSE 8888

CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root"]
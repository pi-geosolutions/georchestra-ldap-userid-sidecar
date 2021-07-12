SHELL := /bin/bash
IMAGE=pigeosolutions/georchestra-ldap-userid-job
REV=`git rev-parse --short HEAD`
DATE=`date +%Y%m%d-%H%M`
#DATE=`date +%Y%m%d`

all: pull-deps docker-build docker-push

pull-deps:
	docker pull python:3-alpine

docker-build:
	docker build  -t ${IMAGE}:${DATE}-${REV} . ;\
	echo built ${IMAGE}:${DATE}-${REV}

docker-push:
	docker push ${IMAGE}:${DATE}-${REV} ;\
	echo pushed ${IMAGE}:${DATE}-${REV}

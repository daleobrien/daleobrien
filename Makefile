# The status page at status.do.id.au lives in site/.
#   make serve    serve site/ at http://localhost:8000
#   make deploy   upload site/ to the status.do.id.au bucket (needs AWS credentials)

BUCKET_PATH ?= s3://status-do-id-au/web/static/
PORT ?= 8000

.PHONY: serve deploy
serve:
	cd site && python3 -m http.server $(PORT)

deploy:
	aws s3 sync site/ $(BUCKET_PATH) --delete --cache-control no-cache

# The status page at status.do.id.au lives in site/ (readable source).
#   make build    copy site/ to dist/, squeezing the HTML (tools/minify.py)
#   make serve    build, then serve dist/ at http://localhost:8000
#   make deploy   build, then upload dist/ to the status.do.id.au bucket (needs AWS credentials)

BUCKET_PATH ?= s3://status-do-id-au/web/static/
PORT ?= 8000

.PHONY: build serve deploy
build:
	python3 tools/minify.py site dist

serve: build
	cd dist && python3 -m http.server $(PORT)

deploy: build
	aws s3 sync dist/ $(BUCKET_PATH) --delete --cache-control no-cache

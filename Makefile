# The status page at status.do.id.au lives in site/ (readable source).
#   make build    build site/ into dist/ (tools/build.py): hashed CSS, script and faces
#   make serve    build, then serve dist/ at http://localhost:8000
#   make deploy   build, then upload dist/ to the status.do.id.au bucket (needs AWS credentials)

BUCKET_PATH ?= s3://status-do-id-au/web/static/
PORT ?= 8000
CACHE_FOREVER := public, max-age=31536000, immutable

.PHONY: build serve deploy
build:
	python3 tools/build.py site dist

serve: build
	cd dist && python3 -m http.server $(PORT)

# Hashed files first (cached for a year: a change gives a new name), then the page
# (always checked), so it never points at a file that isn't there yet. Last,
# anything not in this build (old hashed names) is deleted.
deploy: build
	aws s3 cp dist/ $(BUCKET_PATH) --recursive --exclude index.html --cache-control "$(CACHE_FOREVER)"
	aws s3 cp dist/index.html $(BUCKET_PATH) --cache-control no-cache
	aws s3 sync dist/ $(BUCKET_PATH) --delete --size-only

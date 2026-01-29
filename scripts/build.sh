#!/bin/bash
set -e

echo "Building Alarm Investigator Lambda package..."

# Clean previous build
rm -rf dist/
mkdir -p dist/package

# Install dependencies
pip install -r requirements.txt -t dist/package/

# Copy source code
cp -r src/alarm_investigator dist/package/

# Create zip
cd dist/package
zip -r ../lambda.zip .
cd ../..

echo "Build complete: dist/lambda.zip"
ls -lh dist/lambda.zip

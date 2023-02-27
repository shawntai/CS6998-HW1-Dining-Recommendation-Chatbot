pip3 install --target ./package requests-aws4auth opensearch-py python-dotenv
cd package
zip -r ../lf2.zip .
cd ../
zip lf2.zip lf2.py
aws lambda update-function-code --function-name LF2 --zip-file fileb://lf2.zip
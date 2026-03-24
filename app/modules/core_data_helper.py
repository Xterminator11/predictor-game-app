import pandas as pd
import boto3
import botocore
import re
import json
from modules.util_app import get_bucket_name

BUCKET_NAME = get_bucket_name()


def get_all_data_from_bucket():

    ## Add headers
    # user_name = str(st.session_state.user_name).replace(" ", "").lower()

    client = boto3.client("s3")
    s3_object_list = []

    bucket = BUCKET_NAME

    paginator = client.get_paginator("list_objects")
    page_iterator = paginator.paginate(Bucket=bucket)
    for page in page_iterator:
        for obj in page["Contents"]:
            if re.search(r"_([0-9]|[0-9][0-9]).json", obj["Key"]) is not None:
                s3 = boto3.client("s3")
                try:
                    data = s3.get_object(Bucket=BUCKET_NAME, Key=obj["Key"])
                    contents = json.loads(data["Body"].read().decode("utf-8"))
                    # print(contents)
                    s3_object_list.append(contents)

                except botocore.exceptions.ClientError as e:
                    if e.response["Error"]["Code"] == "404":
                        continue
                    else:
                        continue

    data_frame = pd.DataFrame(s3_object_list)
    return data_frame


if __name__ == "__main__":
    data_frame = get_all_data_from_bucket()
    print(data_frame)

    df = data_frame[
        (data_frame["MatchId"] == 6) & (data_frame["UserName"] == "amanverma")
    ]
    print(df["Selections"])


import argparse
parser = argparse.ArgumentParser()

parser.add_argument("-j", help="json file from product recognition results")
args = parser.parse_args()

def crop_images(json_product_recongnition):
    # This function reads a file containing the results from a product recognition API call.
    # From each image, it generates a separate cropped image containing each of the product recognized.
    # The images are stored in a subfolder called 'crop'.
    #
    # The input images and the results are stored in Google Cloud Storage

    from PIL import Image
    import os
    import json
    from google.cloud import storage
    from urllib.parse import urlparse
    from io import BytesIO

    # Open json file, read jsonl
    with open(args.j, 'r') as json_file:
        json_list = list(json_file)

    # For each image in the json results
    for json_str in json_list:
        json_data = json.loads(json_str)

        # Extract bucket name, file name, extension
        image_uri = json_data["imageUri"]
        gcs = urlparse(image_uri, allow_fragments=False)
        bucket_name = gcs.netloc
        image_path = gcs.path.lstrip('/')
        (im_name, im_ext) = os.path.splitext(image_path)

        # Opens image
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.get_blob(image_path)  
        im = Image.open(BytesIO(blob.download_as_bytes()))

        width, height = im.size
        im_counter = 0

        for crop in json_data["productRecognitionAnnotations"]:
            # Calculate position of bounding box in image
            x_min = width * crop["productRegion"]["boundingBox"]["xMin"]
            y_min = height * crop["productRegion"]["boundingBox"]["yMin"]
            x_max = width * crop["productRegion"]["boundingBox"]["xMax"]
            y_max = height * crop["productRegion"]["boundingBox"]["yMax"]

            # Crop image
            im_c = im.crop((x_min, y_min, x_max, y_max))

            # TO DO: Find a way to upload directly to to GCS
            # Save cropped images in GCS
            im_c.save(im_name+'-'+str(im_counter)+im_ext)
            blob_c = bucket.blob('crop/'+im_name+'-'+str(im_counter)+im_ext)
            blob_c.upload_from_filename(im_name+'-'+str(im_counter)+im_ext)
            os.remove(im_name+'-'+str(im_counter)+im_ext)

            im_counter = im_counter + 1


if __name__ == '__main__':

    crop_images(args.j)

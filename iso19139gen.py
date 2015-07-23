#!/usr/bin/env python
from __future__ import print_function
import lxml.etree as etree 
import uuid
import datetime
import gdal
import argparse
import os.path

ns = {
    'gco': 'http://www.isotc211.org/2005/gco',
    'gmd': 'http://www.isotc211.org/2005/gmd',
}

def go(template, img_file, out_file, title=None):
    
    # Setup the parser and open the file
    schema_root = etree.parse(os.path.dirname(__file__) + \
        "/iso19139.anzlic/schema/gmd/gmd.xsd")
    schema = etree.XMLSchema(schema_root)
    parser = etree.XMLParser(schema = schema)
    tree = etree.parse(template, parser)
    
    # File ID
    fid_cs = tree.find("gmd:fileIdentifier", ns).find("gco:CharacterString", ns)
    if fid_cs.text is None:
        fid_uuid = str(uuid.uuid4())
        print("Adding gmd:fileIdentifier ", fid_uuid)
        fid_cs.text = fid_uuid
    else:
        print("Existing gmd:fileIdentifier ", fid_cs.text)
    
    # Update the metadata date
    ds_dt = tree.find("gmd:dateStamp", ns).find("gco:DateTime", ns)
    ds_text = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    print("Adding gmd:dateStamp ", ds_text)
    ds_dt.text = ds_text
    
    # Update the title if given
    if title is not None:
        ti_cs = tree.find(".//gmd:title", ns).find("gco:CharacterString", ns)
        ti_text = title
        print("Adding gmd:title ", ti_text)
        ti_cs.text = ti_text
    
    # Update the extent
    gdal_ds = gdal.Open(img_file)
    proj = gdal_ds.GetProjection()
    geot = gdal_ds.GetGeoTransform()
    extent = [geot[0], geot[0] + geot[1] * gdal_ds.RasterXSize, \
              geot[3], geot[3] + geot[5] * gdal_ds.RasterYSize]
    tags = ["westBoundLongitude", "eastBoundLongitude", \
            "northBoundLatitude", "southBoundLatitude"]
    for i in range(4):
        print("gmd:" + tags[i])
        bl_dec = tree.find(".//gmd:" + tags[i], ns).find("gco:Decimal", ns)
        bl_text = str(extent[i])
        print("Adding gmd:" + tags[i] + " ", bl_text)
        bl_dec.text = bl_text
        
    # Write file
    tree.write(out_file)
    print("Written to ", out_file)
    
    # Revalidate
    etree.parse(out_file, parser)
    print("Validation OK")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(\
        description='Produce ISO19139 metadata for an image using a template.')
    parser.add_argument("template", help="template ISO19139 metadata XML file")
    parser.add_argument("img_file", help="georeferenced image file")
    parser.add_argument("out_file", help="Output XML metadata file")
    #parser.add_argument("title", help="Metadata title for the image")
    
    args = parser.parse_args()
    go(args.template, args.img_file, args.out_file) #, args.title)

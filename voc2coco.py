#coding=utf-8

#author:hemin
#date:2020/3/27

import xml.etree.ElementTree as ET
import os
import json
import shutil


coco = dict()
coco['images'] = []
coco['type'] = 'instances'
coco['annotations'] = []
coco['categories'] = []

category_set = dict()
image_set = set()

category_item_id = -1
image_id = 20180000000
annotation_id = 0


def addCatItem(name):
    global category_item_id
    category_item = dict()
    category_item['supercategory'] = 'none'
    category_item_id += 1
    category_item['id'] = category_item_id
    category_item['name'] = name
    coco['categories'].append(category_item)
    category_set[name] = category_item_id
    return category_item_id


def addImgItem(file_name, size):
    global image_id
    if file_name is None:
        raise Exception('Could not find filename tag in xml file.')
    if size['width'] is None:
        raise Exception('Could not find width tag in xml file.')
    if size['height'] is None:
        raise Exception('Could not find height tag in xml file.')
    image_id += 1
    image_item = dict()
    image_item['id'] = image_id
    image_item['file_name'] = file_name
    image_item['width'] = size['width']
    image_item['height'] = size['height']
    coco['images'].append(image_item)
    image_set.add(file_name)
    return image_id


def addAnnoItem(object_name, image_id, category_id, bbox):
    global annotation_id
    annotation_item = dict()
    annotation_item['segmentation'] = []
    seg = []
    # bbox[] is x,y,w,h
    # left_top
    seg.append(bbox[0])
    seg.append(bbox[1])
    # left_bottom
    seg.append(bbox[0])
    seg.append(bbox[1] + bbox[3])
    # right_bottom
    seg.append(bbox[0] + bbox[2])
    seg.append(bbox[1] + bbox[3])
    # right_top
    seg.append(bbox[0] + bbox[2])
    seg.append(bbox[1])

    annotation_item['segmentation'].append(seg)

    annotation_item['area'] = bbox[2] * bbox[3]
    annotation_item['iscrowd'] = 0
    annotation_item['ignore'] = 0
    annotation_item['image_id'] = image_id
    annotation_item['bbox'] = bbox
    annotation_item['category_id'] = category_id
    annotation_id += 1
    annotation_item['id'] = annotation_id
    coco['annotations'].append(annotation_item)


def parseXmlFiles(xml_path):
    for f in os.listdir(xml_path):
        if not f.endswith('.xml'):
            continue

        bndbox = dict()
        size = dict()
        current_image_id = None
        current_category_id = None
        file_name = None
        size['width'] = None
        size['height'] = None
        size['depth'] = None

        xml_file = os.path.join(xml_path, f)
        print(xml_file)

        tree = ET.parse(xml_file)
        root = tree.getroot()
        if root.tag != 'annotation':
            raise Exception('pascal voc xml root element should be annotation, rather than {}'.format(root.tag))

        # elem is <folder>, <filename>, <size>, <object>
        for elem in root:
            current_parent = elem.tag
            current_sub = None
            object_name = None

            if elem.tag == 'folder':
                continue

            if elem.tag == 'filename':
                file_name = f.split(".")[0]+".jpg"


            elif current_image_id is None and file_name is not None and size['width'] is not None:
                if file_name not in image_set:
                    current_image_id = addImgItem(file_name, size)
                    print('add image with {} and {}'.format(file_name, size))
                else:
                    raise Exception('duplicated image: {}'.format(file_name))
            for subelem in elem:
                bndbox['xmin'] = None
                bndbox['xmax'] = None
                bndbox['ymin'] = None
                bndbox['ymax'] = None

                current_sub = subelem.tag
                if current_parent == 'object' and subelem.tag == 'name':
                    object_name = subelem.text
                    if object_name not in category_set:
                        current_category_id = addCatItem(object_name)
                    else:
                        current_category_id = category_set[object_name]

                elif current_parent == 'size':
                    if size[subelem.tag] is not None:
                        raise Exception('xml structure broken at size tag.')
                    size[subelem.tag] = int(subelem.text)

                for option in subelem:
                    if current_sub == 'bndbox':
                        if bndbox[option.tag] is not None:
                            raise Exception('xml structure corrupted at bndbox tag.')
                        bndbox[option.tag] = int(option.text)

                if bndbox['xmin'] is not None:
                    if object_name is None:
                        raise Exception('xml structure broken at bndbox tag')
                    if current_image_id is None:
                        raise Exception('xml structure broken at bndbox tag')
                    if current_category_id is None:
                        raise Exception('xml structure broken at bndbox tag')
                    bbox = []
                    # x
                    bbox.append(bndbox['xmin'])
                    # y
                    bbox.append(bndbox['ymin'])
                    # w
                    bbox.append(bndbox['xmax'] - bndbox['xmin'])
                    # h
                    bbox.append(bndbox['ymax'] - bndbox['ymin'])
                    print('add annotation with {},{},{},{}'.format(object_name, current_image_id, current_category_id,
                                                                   bbox))
                    addAnnoItem(object_name, current_image_id, current_category_id, bbox)


'''
:param dataDir:  数据的格式：
                    -VOCdevkit
                        -VOC_***1
                            - Annotations
                            - JPEGImages
                            - labels
                            - MAIN
:param saveDir:  数据格式：
                    -COCOdevkit
                        -annotations   标注文件
                        -
                        
:param rate: 
:return: 
'''


def splitAndCopyData(dataDir, saveDir, rate=[0.8, 0.2]):

    train = os.path.join(saveDir,"train")
    if not os.path.exists(train):
        os.mkdir(train)

    test = os.path.join(saveDir, "test")
    if not os.path.exists(test):
        os.mkdir(test)

    annottrain = os.path.join(saveDir,"Annotrain")
    if not os.path.exists(annottrain):
        os.mkdir(annottrain)

    annottest = os.path.join(saveDir, "Annotest")
    if not os.path.exists(annottest):
        os.mkdir(annottest)


    index = 0
    for folder in os.listdir(datasetdir):
        annotdir = os.path.join(datasetdir,folder, "Annotations")
        imagedir = os.path.join(datasetdir,folder, "JPEGImages")



        images = os.listdir(imagedir)
        splitPoint = int(len(images)*rate[0])

        for i in range(len(images)):
            if images[i].endswith("jpg") or images[i].endswith("png"):
                if i < splitPoint:
                    srcName_i = os.path.join(imagedir, images[i]);
                    srcName_a = os.path.join(annotdir, images[i].split(".")[0] + ".xml" )

                    if os.path.exists(srcName_a) and os.path.exists(srcName_i):
                        #写入训练集
                        dstName_i = os.path.join(train, folder+ "_" + str(index) + "." +images[i].split(".")[1])
                        shutil.copy(srcName_i,dstName_i)
                        dstName_a = os.path.join(annottrain, folder+ "_" + str(index) + "." + ".xml" )
                        shutil.copy(srcName_a,dstName_a)

                else:
                    # 写入测试集

                    srcName_it = os.path.join(imagedir, images[i]);
                    srcName_at = os.path.join(annotdir, images[i].split(".")[0] + ".xml")
                    if os.path.exists(srcName_at) and os.path.exists(srcName_it):
                        dstName_it = os.path.join(test, folder + "_" + str(index) + "." + images[i].split(".")[1])
                        shutil.copy(srcName_it, dstName_it)
                        dstName_at = os.path.join(annottest, folder + "_" + str(index) + "." + "xml")
                        shutil.copy(srcName_at, dstName_at)

                index = index +1



if __name__ == '__main__':
    datasetdir = "E:\\workgit\\objectdetectdata\\objectdetect_train\\VOCdevkit"
    saveDir = "E:\\workgit\\objectdetectdata\\objectdetect_train\\COCOdevkit"
    #复制并划分数据集的比例,训练
    splitRata = [0.8, 0.2]
    #划分并合并数据集合
    # splitAndCopyData(datasetdir, saveDir, splitRata)

    xml_path_test = 'E:\\workgit\\objectdetectdata\\objectdetect_train\\COCOdevkit\\Annotest'  # 这是xml文件所在的地址
    xml_path_train = 'E:\\workgit\\objectdetectdata\\objectdetect_train\\COCOdevkit\\Annotrain'  # 这是xml文件所在的地址
    json_file = 'E:\\workgit\\objectdetectdata\\objectdetect_train\\COCOdevkit\\train.json'  # 这是你要生成的json文件
    parseXmlFiles(xml_path_train)  # 只需要改动这两个参数就行了
    json.dump(coco, open(json_file, 'w'))

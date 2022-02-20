import os
import json
import glob
import argparse

from tqdm import tqdm
import xml.etree.ElementTree as element_tree


def get_args():
    parser = argparse.ArgumentParser(
        description="Convert Pascal VOC annotation to COCO format.")

    parser.add_argument(
        "xml_dir",
        help="Directory path to xml files.",
        type=str,
        default='Annotations',
    )
    parser.add_argument(
        "json_file",
        help="Output COCO format json file.",
        type=str,
        default='output.json',
    )

    parser.add_argument(
        "--start_image_id",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--start_bbox_id",
        help="Bounding Box start ID.",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--category",
        help="Specify a category list.",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--indent",
        help="COCO format json indent.",
        type=int,
        default=None,
    )
    parser.add_argument(
        "--bbox_offset",
        help="Bounding Box offset.",
        type=int,
        default=-1,
    )

    args = parser.parse_args()

    return args


def main():
    # 引数取得
    args = get_args()

    xml_dir = args.xml_dir
    json_file = args.json_file

    start_image_id = args.start_image_id
    start_bbox_id = args.start_bbox_id
    category_txt_path = args.category
    indent = args.indent
    bbox_offset = args.bbox_offset

    # Pascal VOC XMLファイルリスト取得
    xml_files = glob.glob(os.path.join(xml_dir, "*.xml"))

    # 事前定義のカテゴリーリストを取得
    predefine_categories = None
    if category_txt_path is not None:
        with open(category_txt_path, 'r') as f:
            category_list = f.readlines()
            predefine_categories = {
                name.rstrip('\n'): i
                for i, name in enumerate(category_list)
            }

    # カテゴリーリスト生成
    if predefine_categories is not None:
        categories = predefine_categories
    else:
        categories = get_categories(xml_files)

    # Pascal VOC → COCO 変換
    print("Number of xml files: {}".format(len(xml_files)))

    json_dict = convert_xml_to_json(
        xml_files,
        categories,
        start_image_id,
        start_bbox_id,
        bbox_offset,
    )

    # JSON保存
    if os.path.dirname(json_file):
        os.makedirs(os.path.dirname(json_file), exist_ok=True)

    with open(json_file, "w") as fp:
        json_text = json.dumps(json_dict, indent=indent)
        fp.write(json_text)

    print("Success: {}".format(json_file))


def get_categories(xml_files):
    classes_names = []

    # 全XMLのobjectからnameを取得
    for xml_file in xml_files:
        tree = element_tree.parse(xml_file)
        root = tree.getroot()

        for member in root.findall("object"):
            classes_names.append(member[0].text)

    # 重複を削除してソート
    classes_names = list(set(classes_names))
    classes_names.sort()

    # Dict形式に変換
    categories = {name: i + 1 for i, name in enumerate(classes_names)}

    return categories


def get_element(root, name, length=None):
    # 指定タグの値を取得
    vars = root.findall(name)

    # 長さチェック
    if length is not None:
        if len(vars) == 0:
            raise ValueError("Can not find %s in %s." % (name, root.tag))
        if length > 0 and len(vars) != length:
            raise ValueError(
                "The size of %s is supposed to be %d, but is %d." %
                (name, length, len(vars)))

        if length == 1:
            vars = vars[0]

    return vars


def get_basename_without_ext(filename):
    # 拡張子を含まないファイル名を取得
    basename_without_ext = filename.replace("\\", "/")
    basename_without_ext = os.path.splitext(os.path.basename(filename))[0]

    return str(basename_without_ext)


def get_basename_with_ext(filename):
    # 拡張子を含むファイル名を取得
    basename_with_ext = filename.replace("\\", "/")
    basename_with_ext = os.path.basename(basename_with_ext)

    return str(basename_with_ext)


def convert_xml_to_json(
    xml_files,
    categories=None,
    start_image_id=None,
    start_bbox_id=1,
    bbox_offset=-1,
):
    json_dict = {
        "images": [],
        "type": "instances",
        "annotations": [],
        "categories": []
    }

    bbox_id = start_bbox_id
    if start_image_id is not None:
        image_id_count = start_image_id

    for xml_file in tqdm(xml_files, "Convert XML to JSON"):
        # ルート要素取得
        tree = element_tree.parse(xml_file)
        root = tree.getroot()

        # 画像ファイル名取得
        path = get_element(root, "path")
        if len(path) == 1:
            filename = os.path.basename(path[0].text)
        elif len(path) == 0:
            filename = get_element(root, "filename", 1).text
        else:
            raise ValueError("%d paths found in %s" % (len(path), xml_file))

        # 画像情報取得
        size = get_element(root, "size", 1)
        width = int(get_element(size, "width", 1).text)
        height = int(get_element(size, "height", 1).text)
        if start_image_id is None:
            image_id = get_basename_without_ext(filename)
        else:
            image_id = image_id_count

        # JSON Dict追加
        image_info = {
            "file_name": filename,
            "height": height,
            "width": width,
            "id": image_id,
        }
        json_dict["images"].append(image_info)

        # object情報取得
        for obj in get_element(root, "object"):
            # カテゴリー名取得
            category = get_element(obj, "name", 1).text
            # 初出のカテゴリー名の場合、リストに追加
            if category not in categories:
                new_id = len(categories)
                categories[category] = new_id

            # カテゴリーID取得
            category_id = categories[category]

            # バウンディングボックス情報取得
            bbox = get_element(obj, "bndbox", 1)
            xmin = int(float(get_element(bbox, "xmin", 1).text)) + bbox_offset
            ymin = int(float(get_element(bbox, "ymin", 1).text)) + bbox_offset
            xmax = int(float(get_element(bbox, "xmax", 1).text))
            ymax = int(float(get_element(bbox, "ymax", 1).text))
            assert xmax > xmin
            assert ymax > ymin
            bbox_width = abs(xmax - xmin)
            bbox_height = abs(ymax - ymin)

            # JSON Dict追加
            annotation_info = {
                "area": bbox_width * bbox_height,
                "iscrowd": 0,
                "image_id": image_id,
                "bbox": [xmin, ymin, bbox_width, bbox_height],
                "category_id": category_id,
                "id": bbox_id,
                "ignore": 0,
                "segmentation": [],
            }
            json_dict["annotations"].append(annotation_info)

            bbox_id = bbox_id + 1
            
        if start_image_id is not None:
            image_id_count = image_id_count + 1

    # カテゴリー情報
    for category_name, category_id in categories.items():
        category_info = {
            "supercategory": "none",
            "id": category_id,
            "name": category_name
        }
        json_dict["categories"].append(category_info)

    return json_dict


if __name__ == "__main__":
    main()

# convert_voc_to_coco
Pascal VOC形式のXMLファイルをCOCO形式のJSONファイルへ変換するスクリプト

# Requirement 
* tqdm 4.62.2 or later

# Usage
使用方法は以下です。
```bash
python convert_voc_to_coco.py xml_directory json_filename
```
* --start_image_id<br>
画像IDの採番開始番号<br>
デフォルト：None
* --start_bbox_id<br>
バウンディングボックスのIDの採番開始番号<br>
デフォルト：1
* --category<br>
クラスIDを指定する場合はクラス名を列挙したテキストファイルを指定(例：class_list.txt)<br>
デフォルト：None
* --indent<br>
COCOフォーマットのJSONファイルを出力する際のインデントスペース数<br>
デフォルト：指定なし
* --bbox_offset<br>
COCO形式のバウンディングボックスへ変換する際のオフセット<br>
デフォルト：-1

# Author
高橋かずひと(https://twitter.com/KzhtTkhs)
 
# License 
convert_voc_to_coco is under [Apache-2.0 License](LICENSE).

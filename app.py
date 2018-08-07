import os
import json
from flask import Flask, render_template, jsonify, request, send_from_directory
import requests
import util
app = Flask(__name__)


BASE_DIR = os.path.dirname(app.instance_path)
DATA_DIR = os.path.join(BASE_DIR, 'data')
UPLOAD_DIR = os.path.join(BASE_DIR, 'upload')


@app.route("/")
def editor():
    source = request.args.get('source', default=None)
    file_type = request.args.get('format', default="csv")
    error_msg = None
    warning_msg = None
    file_name = ""
    if source is None:
        headers = ["AAA", "BBB", "CCC"]
    elif source.startswith('file:/'):
        original_file_name = source.split('/')[-1]
        headers = util.get_headers(source, file_type=file_type)
        file_name = source.split('/')[-1].split('.')[0] + "-" + util.get_random_string(4) + "." + source.split('.')[-1]
        if headers == []:
            warning_msg = "Can't parse the source file %s" % source
    else:
        r = requests.get(source, allow_redirects=True)
        if r.status_code == 200:
            original_file_name = source.split('/')[-1]
            fname = source.split('/')[-1].split('.')[0] + "-" + util.get_random_string(4) + "." + source.split('.')[-1]
            file_name = fname
            uploaded_file_dir = os.path.join(UPLOAD_DIR, fname)
            f = open(uploaded_file_dir, 'w')
            f.write(r.content)
            f.close()
            headers = util.get_headers(uploaded_file_dir, file_type=file_type)
            if headers == []:
                warning_msg = "Can't parse the source file %s" % source
        else:
            error_msg = "the source %s can not be accessed" % source
            print error_msg
            headers = []
    f = open(os.path.join(DATA_DIR, "labels.txt"))
    return render_template('editor.html', labels_txt=f.read(), headers=headers, file_name=original_file_name, error_msg=error_msg, warning_msg=warning_msg)


@app.route("/get_properties")
def get_properties():
    concept = request.args.get('concept', default=None)
    if concept:
        concept = concept.strip()
        schema_prop_path = os.path.join(DATA_DIR, 'schema-prop.json')
        print 'schema_prop_path: %s' % schema_prop_path
        f = open(schema_prop_path)
        properties_j = json.loads(f.read())
        if concept in properties_j:
            properties = list(set(properties_j[concept]))
            return jsonify({'properties': properties})
    return jsonify({'properties': []})


@app.route("/generate_mapping", methods=['POST'])
def generate_mapping():
    if 'entity_class' in request.form and 'entity_column' in request.form and 'file_name' in request.form:
        entity_class = request.form['entity_class']
        entity_column = request.form['entity_column']
        file_name = request.form['file_name']
        # print "request form: "
        # print list(request.form.keys())
        mappings = []
        for i in range(len(request.form.keys())):
            key = 'form_key_' + str(i)
            val = 'form_val_' + str(i)
            if key in request.form and val in request.form:
                if request.form[val].strip() != '':
                    element = {"key": request.form[key], "val": request.form[val]}
                    mappings.append(element)
            else:
                break
        # Assuming the file name has at least a single . to separate the file name and the extension
        file_name_without_ext = ".".join(file_name.split('.')[:-1])
        mapping_file_name = file_name_without_ext+".r2rml"
        mapping_file_dir = os.path.join(UPLOAD_DIR, mapping_file_name)
        util.generate_r2rml_mappings(mapping_file_dir, file_name, entity_class, entity_column, mappings)
        f = open(mapping_file_dir)
        mapping_content = f.read()
        # return render_template('msg.html', msg=mapping_content)
        return send_from_directory(UPLOAD_DIR, mapping_file_name, as_attachment=True)
    else:
        return render_template('msg.html', warning_msg='missing values ... make sure to use our editor')


if __name__ == '__main__':
   app.run(debug=True)
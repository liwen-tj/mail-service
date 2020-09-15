from flask import Blueprint, request, jsonify
from db import getMailLists, getOneMailList, getMessages
data = Blueprint('data', __name__)


@data.route('/get_all_maillists', methods=['GET'])
def getProjectsMaillists():
    ret = getMailLists()
    return jsonify(ret)


@data.route('/get_one_maillists', methods=['GET'])
def getProjectMailList():
    params = request.args.to_dict()
    ret = getOneMailList(params['project'])
    return jsonify(ret)


@data.route('/get_messages', methods=['GET'])
def getProjectMessages():
    params = request.args.to_dict()
    ret = getMessages(params)
    return jsonify(ret)

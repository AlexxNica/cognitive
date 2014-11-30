from ..models import Experiment, Component, Workflow
from ..serializers import WorkflowSerializer
from ..views import send_response 
from rest_framework import viewsets
from rest_framework.renderers import JSONRenderer
from datetime import datetime
from numpy import genfromtxt
import numpy as np
from pandas import *
import threading
import json

class myThread (threading.Thread):
    def __init__(self, threadID, name, experiment):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.experiment = experiment

    def run(self):
        print "Run called for thread name", self.name
        graph_data = [[1,[]],[2,[1]],[3,[2]],[4,[2,3]],[5,[4]],[6,[4]] ,[7,[6]], [8,[7]], [9,[8]],[10,[9]],[11,[10]],[12,[11]]] 
        #input_data = None 
        input_data = DataFrame
        feature_names = None
        feature_types = None
        for data in graph_data:
            component_id = data[0]
            print "Id ", component_id
            comp = Component.objects.get(pk= component_id)
            print "Component_id" , component_id, " " ,comp.operation_type 
            op = comp.operation_type
            if op.function_type == 'Create':
                if op.function_arg == 'Table':
                    if op.function_subtype == 'Input':
                        filename = op.function_subtype_arg
                        #input_data = genfromtxt(filename, delimiter=',', dtype = None)
                        #feature_names = input_data[0]
                        #input_data = input_data[1:]
                        input_data = read_csv(filename)
                        feature_names = input_data.columns
                if op.function_arg == 'Row':
                    if op.function_subtype == 'Row':
                        row_values = json.loads(op.function_subtype_arg)
                        #arr = np.array(row_values)
                        #input_data = np.vstack((input_data,row_values))
                        input_data.loc[len(input_data)+1]= row_values
                if op.function_arg == 'Model':
                    if op.function_subtype == 'Train-Test':
                        params = json.loads(op.function_subtype_arg)
                        train_data_percentage = int(params["train_data_percentage"])
                        target_column = int(params["target_column"])
                        model_type = op.function_arg_id
                        print model_type, train_data_percentage,target_column
            if op.function_type == 'Update' :
                if op.function_arg == 'Table':
                    if op.function_subtype == 'Metadata':
                        feature_types = json.loads(op.function_subtype_arg)
                        print "Feature Names" ,feature_names, " Feature_types ", feature_types
                        
                if op.function_arg == 'Column':
                    if op.function_subtype == 'Add':
                        constant_value = float(op.function_subtype_arg)
                        column_id = float(op.function_arg_id)
                        column_name = input_data.columns[column_id]
                        input_data[column_name] = input_data[column_name] + constant_value
                        #input_data[:,column_id] = input_data[:,column_id] + constant_value
                    if op.function_subtype == 'Sub':
                        constant_value = float(op.function_subtype_arg)
                        column_id = float(op.function_arg_id)
                        column_name = input_data.columns[column_id]
                        input_data[column_name] = input_data[column_name] - constant_value
                        #input_data[:,column_id] = input_data[:,column_id] - constant_value
                    if op.function_subtype == 'Mult':
                        constant_value = float(op.function_subtype_arg)
                        column_id = float(op.function_arg_id)
                        column_name = input_data.columns[column_id]
                        input_data[column_name] = input_data[column_name] * constant_value
                        #input_data[:,column_id] = input_data[:,column_id] * constant_value
                    if op.function_subtype == 'Div':
                        constant_value = float(op.function_subtype_arg)
                        column_id = float(op.function_arg_id)
                        column_name = input_data.columns[column_id]
                        input_data[column_name] = input_data[column_name] / constant_value
                        #input_data[:,column_id] = input_data[:,column_id] / constant_value
                    if op.function_subtype == 'Normalize':
                        column_id = float(op.function_arg_id)
                        column_name = input_data.columns[column_id]
                        sum_array = input_data.sum(axis=0)
                        normalization_value = sum_array[column_name]
                        #sum_array = np.sum(input_data, axis = 0)
                        #constant_value = sum_array[column_id]
                        #input_data[:,column_id] = input_data[:,column_id] / constant_value
                        input_data[column_name] = input_data[column_name] / normalization_value
            if op.function_type == 'Filter' :
                if op.function_arg == 'Table':
                    if op.function_subtype == 'Project':
                        column_id_list = json.loads(op.function_arg_id)
                        excluded_columns = range(len(input_data.columns))
                        for elem in column_id_list:
                            excluded_columns.remove(elem)
                        input_data = input_data.drop(input_data.columns[excluded_columns], axis=1)
                    if op.function_subtype == 'RemoveDup':
                        column_id_list = json.loads(op.function_arg_id)
                        column_name_list = []
                        for elem in column_id_list:
                            column_name_list.append(input_data.columns[elem])
                        input_data = input_data.drop_duplicates(subset = column_name_list) 
                    if op.function_subtype == 'RemoveMissing':
                        if op.function_subtype_arg == 'Replace_mean':
                            input_data = input_data.fillna(input_data.mean())
                        if op.function_subtype_arg == 'Replace_median':
                            input_data = input_data.fillna(input_data.median())
                        if op.function_subtype_arg == 'Replace_mode':
                            input_data = input_data.fillna(input_data.mode())
                        if op.function_subtype_arg == 'Drop_row':
                            input_data = input_data.dropna(axis = 0)
            print "Data"
            print input_data
            print "Data Type"
            print input_data.dtypes
                         

class WorkFlowViewSet(viewsets.ViewSet):
    
    def list(self, request):
        exp = Workflow.objects.all()
        serializer = WorkflowSerializer(exp, many=True)
        return send_response(request.method,serializer)

    def retrieve(self, request, pk=None):
        workflow = Workflow.objects.get(pk=pk)
        serializer = WorkflowSerializer(workflow)
        return send_response(request.method,serializer)

    def create(self,request):
        data = json.loads(JSONRenderer().render(request.DATA))
        exp_id = int(data["experiment"])
        print "Experiment ", exp_id
        serializer = WorkflowSerializer(data=request.DATA)
        if serializer.is_valid():
           serializer.save()
        thread = myThread(1, "WorkFlow Thread", exp_id)
        thread.start() 
        return send_response(request.method,serializer)
    
    def update(self,request, pk=None):
        exp = Workflow.objects.get(pk=pk)
        serializer = WorkflowSerializer(exp,data=request.DATA)
        if serializer.is_valid():
            serializer.save()
        return send_response(request.method,serializer)

    def destroy(self, request, pk=None):
        exp = Workflow.objects.get(pk=pk)
        serializer = None
        exp.delete()
        return send_response(request.method,serializer)
        

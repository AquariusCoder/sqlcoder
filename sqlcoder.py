# -*- coding: utf-8 -*-
"""
Copyright 2015 flw_dream@126.com

Licensed under the Apache License, Version 2.0 (the "License")
 
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""

import os, sys
import cx_Oracle

os.environ['NLS_LANG'] = 'SIMPLIFIED CHINESE_CHINA.UTF8'

# begin custom define ###########################
g_map_type = {
   'VARCHAR2':'SqliteData::DataType::String',
   'NVARCHAR2':'SqliteData::DataType::String',
   'NUMBER':'SqliteData::DataType::Int',
   'DATE':'SqliteData::DataType::TimeStamp',
   'BLOB':'SqliteData::DataType::ByteArray',
}

g_map_type_func = {
   'VARCHAR2':'toString',
   'NVARCHAR2':'toString',
   'NUMBER':'toInt',
   'DATE':'toString',
   'BLOB':'toString',
}

g_map_nullable = {
    'Y':'true',
    'N':'false',
}

g_map_iskey = {
    True:'true',
    False:'false',
}

g_map_sqlfld_strufld = {
    'zoe_std_dict':{
        },
    'zoe_std_dict_item':{},
    'zoe_std_ds':{
        'id':'strId',
        'name':'strName',
        'std_code':'strStdCode',
        'std_name':'strStdName',
        'type':'systemType',
        'parent_id':'strParentId',
        'operator':'strOperator',
        'timestamp':'dtTimeStamp',
        'notes':'strNote',
        'sort_code':'nSortCode',
        'status':'nStatus',
        },
    'zoe_std_data_element':{},
    'zoe_std_segment_catalog':{},
    'zoe_std_segment':{},
    'zoe_std_de_segment_distribute':{},
    'zoe_std_de_dictitem_distribute':{
        'de_id':'strDataElementId',
        'disease_id':'strDiseaseId',
        'dict_id':'lngDictId',
        'dict_item_id':'strDictItemId',
        'segment_id':'strSegmentId',
        'dict_item_alias':'strDictItemAlias',
        'group_no':'lngGroupNo',
        'sort_code':'lngSortCode',
        'prefix':'strPrefix',
        'suffix':'strSuffix',
        'item_name':'strItemName',
        'item_name_position':'strItemNamePosition',
        'template_id':'strTemplateId',
        'template_name':'strTemplateName',
        'timestamp':'strTimeStamp',
        'status':'lngStatus',
        },
}

# end custom define ###########################

class Field(object):
    def __init__(self, name, type, len, nullable, comments='', iskey=False):
        self.name = name
        self.type = type
        self.len = len
        self.nullable = nullable
        self.comments = comments
        self.iskey = iskey
    
class Table(object):
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields
    
class Connect(object):
    def __init__(self, cnn_str):
        self.cnn_str = cnn_str
    
    def get_table(self, table_name):
        cnn = cx_Oracle.connect(self.cnn_str)
        cursor = cnn.cursor()
        
        sqlkey = '''select col.column_name from dba_constraints con, dba_cons_columns col 
                    where con.constraint_name = col.constraint_name and con.constraint_type='P' and col.table_name = '%s' 
                 ''' % table_name.upper()
        cursor.execute(sqlkey)
        keys = cursor.fetchall()
        
        sql = '''select t1.column_name, t1.data_type, t1.data_length, t1.nullable, t2.comments 
                 from dba_tab_columns t1 left join user_col_comments t2
                    on t1.table_name = t2.table_name and t1.column_name = t2.column_name 
                where t1.table_name='%s' ''' % table_name.upper()
        cursor.execute(sql)
        
        fields = []
        for item in cursor.fetchall():
            iskey = True if item[0] in keys else False
            fields.append(Field(item[0], item[1], item[2], item[3], item[4], iskey))
        
        cursor.close()
        cnn.close()
        
        return Table(table_name, fields)
        
class Coder(object):
    '''
    根据需求编写 generate 函数
    '''
    def generate_add_field(self, table, builder, out_path):
        str =''
        for fld in table.fields:
            row = '%s.addField(SqliteField(L"%s", %s, %s, %s, %s));\t// %s\n' % (\
                builder, \
                fld.name.lower(), \
                g_map_type[fld.type], \
                g_map_nullable[fld.nullable], \
                fld.len, \
                g_map_iskey[fld.iskey], \
                fld.comments)
            str += row
        self.__out(str, out_path)
        
    def generate_exec_item(self, table, out_path):
        str =''
        map_name_struct = g_map_sqlfld_strufld[table.name.lower()]
        for fld in table.fields:
            row = 'item.%s = record.field(L"%s").value().%s();\n' % (\
                map_name_struct[fld.name.lower()], \
                fld.name.lower(), \
                g_map_type_func[fld.type])

            str += row
        self.__out(str, out_path)

    def generate_xml_att(self, table, out_path):
        strTemp = '<'
        for fld in table.fields:
            strTemp += '%s = L"" ' % fld.name.lower()
        
        strTemp = strTemp + '></%s>' % table.fields[0].name.lower()
        self.__out(strTemp, out_path)
        
    def generate_xml_tag(self, table, out_path):
        strTemp = '<root>\n'
        for fld in table.fields:
            strTemp += '    <%s><%s>    %s\n' % (fld.name.lower(), fld.name.lower(), fld.comments)

        strTemp = strTemp + '</root>'
        self.__out(strTemp, out_path)

    def generate_get_xml_data(self, table, out_path):
        strTemp = ''
        for fld in table.fields:
            strTemp += 'wstring %s = root[L"%s"].GetData();\n' % (fld.name.lower(), fld.name.lower())

        self.__out(strTemp, out_path)

    def generate_sql_clause(self, table, out_path):
        strTemp = ''
        for fld in table.fields:
            strTemp += 'if(!%s.empty())\n\tosCondition << L" AND T.%s = \'" << %s << L"\' ";\n' % (fld.name.lower(), fld.name.lower(), fld.name.lower())

        self.__out(strTemp, out_path)
    def generate_sql_sel_fields(self, table, out_path):
        strTemp = ''
        for fld in table.fields:
            strTemp += 'T.%s, ' % fld.name.lower()

        self.__out(strTemp, out_path)

    def generate_sel_tag(self, table, out_path):
        strTemp = ''
        for fld in table.fields:
            strTemp += 'vecTag.push_back(L"%s");\n' % fld.name.lower()

        self.__out(strTemp, out_path)
        
    def __out(self, str, out_path):
        file = open(out_path, 'w')
        file.write(str)
        file.close()
        
if __name__ == '__main__':
    def inputparam(index, prompt, default='', options=None, nullable=True):
        if len(sys.argv) > index:
            ret = sys.argv[index]
        else:
            ret = raw_input(prompt)
            
        if ret == '':
            ret = default
        
        if ret == '' and not nullable:
            print 'not allow null\n'
            ret = inputparam(index, prompt, default, options, nullable)
            
        if options is not None and ret not in options.keys():
            print 'select one of the options please!\n'
            ret = inputparam(index, prompt, default, options, nullable)
            
        return ret
    
    generate_opt = {
        '1':'ge_add_field', 
        '2':'ge_exec_item', 
        '3':'ge_xml_att', 
        '4':'ge_xml_tag',
        '5':'ge_get_xml_data',
        '6':'ge_sql_clause',
        '7':'ge_sql_sel_fields',
        '8':'ge_sel_tag'
        }
    strSelTip = 'select operate(defaulat: 1):\n'
    for k, v in generate_opt.items():
        strSelTip += '%s.%s\n' % (k, v)

    cnn_str = inputparam(1, 'input the connect string(zemr/zemr@ZEMR_720): ', 'zemr/zemr@ZEMR_720', None, False)
    table_name = inputparam(2, 'input the table name: ', '', None, False)
    op_index = inputparam(3, strSelTip, '1', generate_opt, False)
    out_path = inputparam(4, 'input the out file path(coder_out.txt): ', 'coder_out.txt', None, False)
    
    op = generate_opt[op_index]
    cnn = Connect(cnn_str)
    table = cnn.get_table(table_name)
    
    coder = Coder()
    if op == 'ge_add_field':
        builder = inputparam(5, 'input the sqlbuilder(m_builder):', 'm_builder', None, False)
        coder.generate_add_field(table, builder, out_path)
    elif op == 'ge_exec_item':
        coder.generate_exec_item(table, out_path)
    elif op == 'ge_xml_att':
        coder.generate_xml_att(table, out_path)
    elif op == 'ge_xml_tag':
        coder.generate_xml_tag(table, out_path)
    elif op == 'ge_get_xml_data':
        coder.generate_get_xml_data(table, out_path)
    elif op == 'ge_sql_clause':
        coder.generate_sql_clause(table, out_path)
    elif op == 'ge_sql_sel_fields':
        coder.generate_sql_sel_fields(table, out_path)
    elif op == 'ge_sel_tag':
        coder.generate_sel_tag(table, out_path)
    

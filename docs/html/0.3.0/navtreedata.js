/*
 @licstart  The following is the entire license notice for the JavaScript code in this file.

 The MIT License (MIT)

 Copyright (C) 1997-2020 by Dimitri van Heesch

 Permission is hereby granted, free of charge, to any person obtaining a copy of this software
 and associated documentation files (the "Software"), to deal in the Software without restriction,
 including without limitation the rights to use, copy, modify, merge, publish, distribute,
 sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in all copies or
 substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
 BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
 DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

 @licend  The above is the entire license notice for the JavaScript code in this file
*/
var NAVTREE =
[
  [ "NSUKit", "index.html", [
    [ "简介", "index.html", "index" ],
    [ "🚀快速开始", "md_markdown_02__quickstart.html", [
      [ "目录", "md_markdown_02__quickstart.html#autotoc_md7", null ],
      [ "1. 环境安装", "md_markdown_02__quickstart.html#md_环境安装", [
        [ "1.1. 环境依赖", "md_markdown_02__quickstart.html#autotoc_md9", null ],
        [ "1.2. 支持的操作系统与平台", "md_markdown_02__quickstart.html#autotoc_md10", null ],
        [ "1.3. 安装", "md_markdown_02__quickstart.html#autotoc_md11", null ]
      ] ],
      [ "2. 基础接口", "md_markdown_02__quickstart.html#md_基础接口", [
        [ "2.1. 片上系统类NSUSoc", "md_markdown_02__quickstart.html#md_片上系统类NSUSoc", [
          [ "2.1.1. 指定协议接口", "md_markdown_02__quickstart.html#md_指定协议接口", null ],
          [ "2.1.2. 发起连接", "md_markdown_02__quickstart.html#md_发起连接", null ]
        ] ],
        [ "2.2. 基于NSUSoc对象的三种交互", "md_markdown_02__quickstart.html#md_基于NSUSoc对象的三种交互", [
          [ "2.2.1 指令寄存器交互", "md_markdown_02__quickstart.html#md_指令寄存器交互", [
            [ "2.2.1.1. 单地址写入/读取", "md_markdown_02__quickstart.html#autotoc_md13", null ],
            [ "2.2.1.2. 片写入/读取", "md_markdown_02__quickstart.html#autotoc_md14", null ],
            [ "2.2.1.3. 单址片写入/读取", "md_markdown_02__quickstart.html#autotoc_md15", null ]
          ] ],
          [ "2.2.2. 指令流交互", "md_markdown_02__quickstart.html#md_指令流交互", [
            [ "2.2.2.1. 配置参数", "md_markdown_02__quickstart.html#autotoc_md16", null ],
            [ "2.2.2.2. 获取参数", "md_markdown_02__quickstart.html#autotoc_md17", null ],
            [ "2.2.2.3. 执行指令", "md_markdown_02__quickstart.html#autotoc_md18", null ]
          ] ],
          [ "2.2.3. 数据流交互", "md_markdown_02__quickstart.html#md_数据流交互", null ]
        ] ]
      ] ]
    ] ],
    [ "进阶使用", "md_markdown_03__professional.html", [
      [ "目录", "md_markdown_03__professional.html#autotoc_md21", null ],
      [ "基本结构", "md_markdown_03__professional.html#autotoc_md23", null ],
      [ "自闭环仿真", "md_markdown_03__professional.html#autotoc_md25", null ],
      [ "数据流交互", "md_markdown_03__professional.html#autotoc_md27", [
        [ "同步方式", "md_markdown_03__professional.html#autotoc_md28", null ],
        [ "异步方式", "md_markdown_03__professional.html#autotoc_md29", null ]
      ] ]
    ] ],
    [ "ICD文件格式", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html", [
      [ "1. ICD指令交互流程", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html#autotoc_md32", [
        [ "1.1. 请求包头", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html#autotoc_md33", null ],
        [ "1.2. 反馈包头", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html#autotoc_md34", null ]
      ] ],
      [ "2. icd.json格式", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html#autotoc_md36", [
        [ "2.1. fpack 参数描述", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html#autotoc_md37", null ],
        [ "2.2. pname 参数名", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html#autotoc_md38", null ],
        [ "2.3. cname 指令名", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html#autotoc_md39", null ],
        [ "2.4. pmap 参数映射", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html#autotoc_md40", null ],
        [ "2.5. cmap 指令映射", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html#autotoc_md41", null ],
        [ "2.6. param 组", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html#md_ICDScheme_param_group", null ],
        [ "2.7. command 组", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html#md_ICDScheme_cmd_group", null ],
        [ "2.8. sequence 组", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html#autotoc_md42", null ]
      ] ],
      [ "3. icd.json示例", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html#autotoc_md44", null ],
      [ "4. icd解析程序", "md__i_c_d_xE6_x96_x87_xE4_xBB_xB6_xE6_xA0_xBC_xE5_xBC_x8F.html#autotoc_md46", null ]
    ] ],
    [ "自定义协议层", "md_markdown_05__custom_protocol_layer.html", [
      [ "自定义接口", "md_markdown_05__custom_protocol_layer.html#autotoc_md49", [
        [ "自定义指令接口", "md_markdown_05__custom_protocol_layer.html#autotoc_md50", null ],
        [ "自定义数据流接口", "md_markdown_05__custom_protocol_layer.html#autotoc_md51", null ]
      ] ]
    ] ],
    [ "自定义处理层", "md_markdown_06__custom_processing_layer.html", [
      [ "icd_paresr", "md_markdown_06__custom_processing_layer.html#md_icd_paresr", [
        [ "icd.json", "md_markdown_06__custom_processing_layer.html#autotoc_md53", null ],
        [ "config(self, **kwargs):", "md_markdown_06__custom_processing_layer.html#autotoc_md54", null ],
        [ "get_param(self, param_name: str, default=0, fmt_type=int):", "md_markdown_06__custom_processing_layer.html#autotoc_md56", null ],
        [ "set_param(self, param_name: str, value, fmt_type=int):", "md_markdown_06__custom_processing_layer.html#autotoc_md57", null ]
      ] ],
      [ "virtual_chnl", "md_markdown_06__custom_processing_layer.html#autotoc_md59", [
        [ "virtual_chnl未开启时", "md_markdown_06__custom_processing_layer.html#autotoc_md60", null ],
        [ "virtual_chnl开启时", "md_markdown_06__custom_processing_layer.html#autotoc_md61", null ]
      ] ]
    ] ],
    [ "协议详解", "md_markdown_07__protocol_details.html", [
      [ "名词解释", "md_markdown_07__protocol_details.html#autotoc_md70", null ]
    ] ],
    [ "NRD FDK", "md_markdown_app_nrd_fdk.html", [
      [ "1. 指令交互", "md_markdown_app_nrd_fdk.html#autotoc_md73", [
        [ "1.1. ICD列表", "md_markdown_app_nrd_fdk.html#autotoc_md74", null ],
        [ "1.2. 指令交互示例", "md_markdown_app_nrd_fdk.html#autotoc_md75", null ]
      ] ],
      [ "2. 寄存器交互", "md_markdown_app_nrd_fdk.html#autotoc_md77", [
        [ "2.1. 寄存器列表", "md_markdown_app_nrd_fdk.html#autotoc_md78", null ],
        [ "2.2. 指令交互示例", "md_markdown_app_nrd_fdk.html#autotoc_md79", null ]
      ] ],
      [ "3. 数据流交互", "md_markdown_app_nrd_fdk.html#autotoc_md81", null ]
    ] ],
    [ "变更记录", "md_markdown__c_h_a_n_g_e_l_o_g.html", [
      [ "v0.3.0 (2023-09-13)", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md84", [
        [ "Feat", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md85", null ]
      ] ],
      [ "v0.2.1 (2023-09-10)", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md86", [
        [ "Feat", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md87", null ]
      ] ],
      [ "v0.2.0 (2023-09-08)", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md88", [
        [ "Feat", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md89", null ]
      ] ],
      [ "v0.1.3 (2023-09-05)", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md90", [
        [ "Feat", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md91", null ]
      ] ],
      [ "v0.1.2 (2023-09-01)", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md92", [
        [ "Feat", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md93", null ]
      ] ],
      [ "v0.1.1 (2023-08-24)", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md94", null ],
      [ "V0.1.0 (2023-08-23)", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md95", [
        [ "Feat", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md96", null ],
        [ "Fix", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md97", null ]
      ] ]
    ] ],
    [ "待办事项列表", "todo.html", null ],
    [ "命名空间", "namespaces.html", [
      [ "命名空间列表", "namespaces.html", null ],
      [ "命名空间成员", "namespacemembers.html", [
        [ "全部", "namespacemembers.html", null ],
        [ "函数", "namespacemembers_func.html", null ]
      ] ]
    ] ],
    [ "类", "annotated.html", [
      [ "类列表", "annotated.html", "annotated_dup" ],
      [ "类索引", "classes.html", null ],
      [ "类继承关系", "hierarchy.html", "hierarchy" ],
      [ "类成员", "functions.html", [
        [ "全部", "functions.html", null ],
        [ "函数", "functions_func.html", null ]
      ] ]
    ] ],
    [ "文件", "files.html", [
      [ "文件列表", "files.html", "files_dup" ]
    ] ]
  ] ]
];

var NAVTREEINDEX =
[
"____init_____8py_source.html"
];

var SYNCONMSG = '点击 关闭 面板同步';
var SYNCOFFMSG = '点击 开启 面板同步';
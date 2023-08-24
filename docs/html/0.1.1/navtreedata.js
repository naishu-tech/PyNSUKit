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
    [ "简介", "index.html", null ],
    [ "🚀快速开始", "md_markdown_2__quickstart.html", [
      [ "目录", "md_markdown_2__quickstart.html#autotoc_md4", null ],
      [ "环境安装", "md_markdown_2__quickstart.html#autotoc_md7", [
        [ "环境依赖", "md_markdown_2__quickstart.html#autotoc_md8", null ],
        [ "安装", "md_markdown_2__quickstart.html#autotoc_md9", null ]
      ] ],
      [ "使用接口", "md_markdown_2__quickstart.html#autotoc_md11", [
        [ "网络指令", "md_markdown_2__quickstart.html#autotoc_md12", null ],
        [ "串口指令", "md_markdown_2__quickstart.html#autotoc_md13", null ],
        [ "PCI-E指令", "md_markdown_2__quickstart.html#autotoc_md14", null ],
        [ "网络数据流", "md_markdown_2__quickstart.html#autotoc_md15", null ],
        [ "PCI-E数据流", "md_markdown_2__quickstart.html#autotoc_md16", null ]
      ] ],
      [ "名词解释", "md_markdown_2__quickstart.html#autotoc_md18", null ],
      [ "工程基本结构", "md_markdown_2__quickstart.html#autotoc_md20", null ]
    ] ],
    [ "进阶使用", "md_markdown_3__professional.html", [
      [ "目录", "md_markdown_3__professional.html#autotoc_md23", null ],
      [ "NSUKit", "md_markdown_3__professional.html#autotoc_md25", [
        [ "NSUKit():", "md_markdown_3__professional.html#autotoc_md26", null ],
        [ "start_command(self, target=None, **kwargs) -> None::", "md_markdown_3__professional.html#autotoc_md27", null ],
        [ "stop_command(self) -> None:", "md_markdown_3__professional.html#autotoc_md28", null ],
        [ "write(self, addr: int, value: bytes) -> bytes:", "md_markdown_3__professional.html#autotoc_md29", null ],
        [ "read(self, addr: int) -> bytes:", "md_markdown_3__professional.html#autotoc_md30", null ],
        [ "bulk_write(self, params: dict) -> list:", "md_markdown_3__professional.html#autotoc_md31", null ],
        [ "bulk_read(self, addrs: list) -> list:", "md_markdown_3__professional.html#autotoc_md32", null ],
        [ "start_stream(self, target=None, **kwargs):", "md_markdown_3__professional.html#autotoc_md34", null ],
        [ "stop_stream(self):", "md_markdown_3__professional.html#autotoc_md35", null ],
        [ "alloc_buffer(self, length, buf: int = None):", "md_markdown_3__professional.html#autotoc_md36", null ],
        [ "free_buffer(self, fd):", "md_markdown_3__professional.html#autotoc_md37", null ],
        [ "get_buffer(self, fd, length):", "md_markdown_3__professional.html#autotoc_md38", null ],
        [ "send_open(self, chnl, fd, length, offset=0):", "md_markdown_3__professional.html#autotoc_md39", null ],
        [ "recv_open(self, chnl, fd, length, offset=0):", "md_markdown_3__professional.html#autotoc_md40", null ],
        [ "wait_dma(self, fd, timeout: int = 0):", "md_markdown_3__professional.html#autotoc_md41", null ],
        [ "break_dma(self, fd):", "md_markdown_3__professional.html#autotoc_md42", null ],
        [ "stream_recv(self, chnl, fd, length, offset=0, stop_event=None, flag=1):", "md_markdown_3__professional.html#autotoc_md43", null ],
        [ "stream_send(self, chnl, fd, length, offset=0, stop_event=None, flag=1):", "md_markdown_3__professional.html#autotoc_md44", null ]
      ] ],
      [ "icd_paresr", "md_markdown_3__professional.html#autotoc_md46", [
        [ "icd.json", "md_markdown_3__professional.html#autotoc_md47", null ],
        [ "config(self, **kwargs):", "md_markdown_3__professional.html#autotoc_md48", null ],
        [ "get_param(self, param_name: str, default=0, fmt_type=int):", "md_markdown_3__professional.html#autotoc_md50", null ],
        [ "set_param(self, param_name: str, value, fmt_type=int):", "md_markdown_3__professional.html#autotoc_md51", null ]
      ] ],
      [ "virtual_chnl", "md_markdown_3__professional.html#autotoc_md53", [
        [ "virtual_chnl未开启时", "md_markdown_3__professional.html#autotoc_md54", null ],
        [ "virtual_chnl开启时", "md_markdown_3__professional.html#autotoc_md55", null ]
      ] ],
      [ "自定义接口", "md_markdown_3__professional.html#autotoc_md57", [
        [ "自定义指令接口", "md_markdown_3__professional.html#autotoc_md58", null ],
        [ "自定义数据流接口", "md_markdown_3__professional.html#autotoc_md59", null ]
      ] ],
      [ "工程详细结构结构", "md_markdown_3__professional.html#autotoc_md61", null ],
      [ "TCPCmdUItf", "md_markdown_3__professional.html#autotoc_md63", null ],
      [ "SerialCmdUItf", "md_markdown_3__professional.html#autotoc_md65", null ],
      [ "PCIECmdUItf", "md_markdown_3__professional.html#autotoc_md67", null ],
      [ "TCPChnlUItf", "md_markdown_3__professional.html#autotoc_md69", null ],
      [ "PCIEChnlUItf", "md_markdown_3__professional.html#autotoc_md71", null ],
      [ "名词解释", "md_markdown_3__professional.html#autotoc_md73", null ]
    ] ],
    [ "v0.1.1 (2023-08-24)", "md_markdown__c_h_a_n_g_e_l_o_g.html", [
      [ "V0.1.0 (2023-08-23)", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md76", [
        [ "Feat", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md77", null ],
        [ "Fix", "md_markdown__c_h_a_n_g_e_l_o_g.html#autotoc_md78", null ]
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
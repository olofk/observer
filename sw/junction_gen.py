#!/usr/bin/python
from fusesoc.capi2.generator import Generator
import os
import shutil
import subprocess

from verilogwriter import Instance, ModulePort, Parameter, Port, VerilogWriter, Wire

class JunctionGenerator(Generator):
    def run(self):
        files = [{'junctions.v' : {'file_type' : 'verilogSource'}}]
        for name, config in self.config.items():
            collector = None
            memfile = None
            if config:
                collector = config.get('collector')
                memfile   = config.get('memfile')
            if not memfile:
                memfile = name+'.hex'
            #Clean out old junctions and copy new from observer root
            shutil.rmtree(name, True)
            junction_src_dir = os.path.join(self.files_root, 'junctions', name)
            if os.path.exists(junction_src_dir):
                shutil.copytree(junction_src_dir, name)
            else:
                os.makedirs(name)

            #Run Makefile if something needs to be made (e.g. C/asm to hex)
            if os.path.exists(os.path.join(name, 'Makefile')):
                subprocess.call(['make', '-C', name])

            #Create junction toplevel
            self.junction_top(name, collector, memfile)
            files.append({os.path.join(name, 'junction.v') : {'file_type' : 'verilogSource'}})
            if os.path.exists(os.path.join(name, memfile)):
                files.append({os.path.join(name, name+'.hex') : {'file_type' : 'user', 'copyto' : name+'.hex' }})

        self.gen_junctions_top(self.config)
        self.add_files(files)

    def gen_junctions_top(self, config):
        junctions = VerilogWriter('junctions')
        junctions.add(ModulePort('i_clk'  , 'input'))
        junctions.add(ModulePort('i_rst'  , 'input'))
        i=0
        muxports = [Port('clk', 'i_clk'),
                    Port('rst', 'i_rst')]

        for name, data in config.items():
            collector = None
            if data:
                collector = data.get('collector')

            junction_ports = [Port('i_clk', 'i_clk'),
                              Port('i_rst', 'i_rst'),]
            if collector == 'gpio':
                junction_ports += [Port('i_gpio', 'i_'+name+'_gpio'),]
            elif collector == 'spi':
                junction_ports += [Port('o_sclk', 'o_'+name+'_sclk'),
                                   Port('o_cs_n', 'o_'+name+'_cs_n'),
                                   Port('o_mosi', 'o_'+name+'_mosi'),
                                   Port('i_miso', 'i_'+name+'_miso'),]
            junction_ports += [
                Port('o_tdata'  , 'tdata'+str(i)),
                Port('o_tlast'  , 'tlast'+str(i)),
                Port('o_tvalid' , 'tvalid'+str(i)),
                Port('i_tready' , 'tready'+str(i)),]
            junctions.add(Instance(name, 'junction_'+name, [], junction_ports))

            if collector == 'gpio':
                junctions.add(ModulePort('i_'+name+'_gpio'  , 'input'))
            elif collector == 'spi':
                junctions.add(ModulePort('o_'+name+'_sclk'  , 'output'))
                junctions.add(ModulePort('o_'+name+'_cs_n'  , 'output'))
                junctions.add(ModulePort('o_'+name+'_mosi'  , 'output'))
                junctions.add(ModulePort('i_'+name+'_miso'  ,  'input'))
            junctions.add(Wire('tdata'+str(i), 8))
            junctions.add(Wire('tlast'+str(i)))
            junctions.add(Wire('tvalid'+str(i)))
            junctions.add(Wire('tready'+str(i)))

            muxports += [Port("s{:02}_axis_tdata".format(i) , 'tdata' +str(i)),
                         Port("s{:02}_axis_tkeep".format(i) , "1'b0"),
                         Port("s{:02}_axis_tvalid".format(i), 'tvalid'+str(i)),
                         Port("s{:02}_axis_tready".format(i), 'tready'+str(i)),
                         Port("s{:02}_axis_tlast".format(i) , 'tlast' +str(i)),
                         Port("s{:02}_axis_tid".format(i)   , "8'd0"),
                         Port("s{:02}_axis_tdest".format(i) , "8'd0"),
                         Port("s{:02}_axis_tuser".format(i) , "1'b0"),]
            i += 1

        junctions.add(ModulePort('o_tdata'  , 'output', 8))
        junctions.add(ModulePort('o_tlast'  , 'output'))
        junctions.add(ModulePort('o_tvalid' , 'output'))
        junctions.add(ModulePort('i_tready' , 'input'))

        muxports += [
            Port('m_axis_tdata ', 'o_tdata'),
            Port('m_axis_tkeep ', ''),
            Port('m_axis_tvalid', 'o_tvalid'),
            Port('m_axis_tready', 'i_tready'),
            Port('m_axis_tlast ', 'o_tlast'),
            Port('m_axis_tid   ', ''),
            Port('m_axis_tdest ', ''),
            Port('m_axis_tuser ', ''),]

        junctions.add(Instance('bcmux', 'bcmux', [Parameter('USER_ENABLE' , '0'),
                                                  Parameter('ARB_TYPE', '"ROUND_ROBIN"')],
                               muxports))
        junctions.write('junctions.v')

    def junction_top(self, name, collector, memfile):
        junction_top = VerilogWriter(name)
        junction_top.add(ModulePort('i_clk'  , 'input'))
        junction_top.add(ModulePort('i_rst'  , 'input'))
        if collector == 'gpio':
            junction_top.add(ModulePort('i_gpio'  ,  'input'))
            junction_top.add(Wire('wb_stb'))
            junction_top.add(Wire('wb_rdt'))
            junction_top.add(Wire('wb_ack'))
            junction_top.add(Instance('collector_gpio', 'gpio', [],
                                      [Port('i_clk'   , 'i_clk'),
                                       Port('i_rst'   , 'i_rst'),
                                       Port('i_dat'   , 'i_gpio'),
                                       Port('i_wb_stb', 'wb_stb'),
                                       Port('o_wb_rdt', 'wb_rdt'),
                                       Port('o_wb_ack', 'wb_ack'),
                                       ]))


        elif collector == 'spi':
            junction_top.add(ModulePort('o_sclk'  , 'output'))
            junction_top.add(ModulePort('o_cs_n'  , 'output'))
            junction_top.add(ModulePort('o_mosi'  , 'output'))
            junction_top.add(ModulePort('i_miso'  ,  'input'))
            junction_top.add(Wire('wb_adr', 32))
            junction_top.add(Wire('wb_dat', 32))
            junction_top.add(Wire('wb_we'))
            junction_top.add(Wire('wb_stb'))
            junction_top.add(Wire('wb_rdt', 32))
            junction_top.add(Wire('wb_ack'))
            junction_top.add(Instance('collector_spi', 'spi', [],
                                      [Port('i_clk'   , 'i_clk'),
                                       Port('i_rst'   , 'i_rst'),
                                       Port('o_sclk'  , 'o_sclk'),
                                       Port('o_cs_n'  , 'o_cs_n'),
                                       Port('o_mosi'  , 'o_mosi'),
                                       Port('i_miso'  , 'i_miso'),
                                       Port('i_wb_adr', 'wb_adr[4:0]'),
                                       Port('i_wb_dat', 'wb_dat'),
                                       Port('i_wb_we' , 'wb_we'),
                                       Port('i_wb_stb', 'wb_stb'),
                                       Port('o_wb_rdt', 'wb_rdt'),
                                       Port('o_wb_ack', 'wb_ack'),
                                       ]))
        junction_top.add(ModulePort('o_tdata'  , 'output', 8))
        junction_top.add(ModulePort('o_tlast'  , 'output'))
        junction_top.add(ModulePort('o_tvalid' , 'output'))
        junction_top.add(ModulePort('i_tready' , 'input'))

        ports = [
            Port('i_clk'   , 'i_clk'),
            Port('i_rst'   , 'i_rst'),]
        if collector == 'spi':
            ports += [
                Port('o_wb_coll_adr', 'wb_adr'),
                Port('o_wb_coll_dat', 'wb_dat'),
                Port('o_wb_coll_we' , 'wb_we'),]
        else:
            ports += [
                Port('o_wb_coll_adr', ''),
                Port('o_wb_coll_dat', ''),
                Port('o_wb_coll_we' , ''),]
        if collector:
            ports.append(Port('o_wb_coll_stb', 'wb_stb'))
        else:
            ports.append(Port('o_wb_coll_stb', ''))
        if collector == 'gpio':
            ports.append(Port('i_wb_coll_rdt', "{31'd0,wb_rdt}"))
        elif collector == 'spi':
            ports.append(Port('i_wb_coll_rdt', 'wb_rdt'))
        else:
            ports.append(Port('i_wb_coll_rdt', "32'd0"))
        if collector:
            ports.append(Port('i_wb_coll_ack', 'wb_ack'))
        else:
            ports.append(Port('i_wb_coll_ack', "1'b0"))
        ports += [
            Port('o_tdata' , 'o_tdata'),
            Port('o_tlast' , 'o_tlast'),
            Port('o_tvalid', 'o_tvalid'),
            Port('i_tready', 'i_tready'),
        ]

        junction_top.add(Instance('base', 'base',
                                  [Parameter('memfile', '"'+memfile+'"')],
                                  ports))

        junction_top.write(os.path.join(name, 'junction.v'))

g = JunctionGenerator()
g.run()
g.write()

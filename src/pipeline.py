"""
   A pipeline example that uses intergrates several interfaces to
   perform a first and second level analysis on a two-subject data
   set. 
"""
from locale import normalize
from nipype.interfaces.fsl.base import NEW_FSLCommand
from nipype.interfaces.freesurfer.base import NEW_FSCommand


"""
1. Tell python where to find the appropriate functions.
"""

import nipype.interfaces.io as nio           # Data i/o 
import nipype.interfaces.spm as spm          # spm
import nipype.interfaces.matlab as mlab      # how to run matlab
import nipype.interfaces.fsl as fsl          # fsl
import nipype.pipeline.node_wrapper as nw    # nodes for pypelines
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.rapidart as ra      # artifact detection
import nipype.algorithms.modelgen as model   # model specification
import nipype.algorithms.misc as misc
import os                                    # system functions
from nipype.interfaces.base import Bunch
from copy import deepcopy
from functional import functional_nodes

#####################################################################
# Preliminaries

"""
1b. Confirm package dependencies are installed.  (This is only for the
tutorial, rarely would you put this in your own code.)
"""
from nipype.utils.misc import package_check

package_check('numpy', '1.3', 'tutorial1')
package_check('scipy', '0.7', 'tutorial1')
package_check('networkx', '1.0', 'tutorial1')
package_check('IPython', '0.10', 'tutorial1')

NEW_FSLCommand.set_default_outputtype('NIFTI')
NEW_FSCommand.set_default_subjectsdir('/home/filo/data/fs/')

"""
2. Setup any package specific configuration. The output file format
   for FSL routines is being set to uncompressed NIFTI and a specific
   version of matlab is being used. The uncompressed format is
   required because SPM does not handle compressed NIFTI.
"""

# setup the way matlab should be called
mlab.MatlabCommandLine.matlab_cmd = "matlab -nodesktop -nosplash"

"""
3. The following lines of code sets up the necessary information
   required by the datasource module. It provides a mapping between
   run numbers (nifti files) and the mnemonic ('struct', 'func',
   etc.,.)  that particular run should be called. These mnemonics or
   fields become the output fields of the datasource module. In the
   example below, run 'f3' is of type 'func'. The 'f3' gets mapped to
   a nifti filename through a template '%s.nii'. So 'f3' would become
   'f3.nii'.
"""

# The following lines create some information about location of your
# data. 
data_dir = os.path.abspath('../data')
subject_list = ['pilot1']
# The following info structure helps the DataSource module organize
# nifti files into fields/attributes of a data object. With DataSource
# this object is of type Bunch.
info = dict(finger_tapping_func = ['5_finger_tapping'],
            finger_foot_lips_func = ['6_finger_foot_lips'],
            silent_verb_generation = ['3_silent_verb_generation'],
            line_bisection = ['2_line_bisection'],
            struct = ['fs/mri/orig'],
            segmentation = ['fs/mri/aparc+aseg'])

######################################################################
# Setup preprocessing pipeline nodes

"""
4. Setup various nodes for preprocessing the data. 
"""

"""
   a. Setting up an instance of the interface
   :class:`nipype.interfaces.io.DataSource`. This node looks into the
   directory containing Nifti files and returns pointers to the files
   in a structured format as determined by the field/attribute names
   provided in the info structure above. The
   :class:`nipype.pipeline.NodeWrapper` module wraps the interface
   object and provides additional housekeeping and pipeline specific
   functionality. 
"""
datasource = nw.NodeWrapper(interface=nio.SubjectSource(), diskbased=False)
datasource.inputs.base_directory = data_dir
datasource.inputs.file_layout = '%s.nii'
datasource.inputs.subject_info = info


"""
   b. Setting up iteration over all subjects. The following line is a
   particular example of the flexibility of the system.  The  variable
   `iterables` for datasource tells the pipeline engine that it should
   repeat any of the processes that are descendents of the datasource
   process on each of the iterable items. In the current example, the
   entire first level preprocessing and estimation will be repeated
   for each subject contained in subject_list.
"""
datasource.iterables = ('subject_id', subject_list)

skullstrip = nw.NodeWrapper(interface=fsl.Bet(), diskbased=True)
skullstrip.inputs.mask = True

#segment = nw.NodeWrapper(interface=spm.Segment(), diskbased=True)
#segment.inputs.gm_output_type = [1, 1, 1]
#segment.inputs.wm_output_type = [1, 1, 1]
#segment.inputs.csf_output_type = [1, 1, 1]

fingertappingSkip = 4
FFLSkip = 4
SVGSkip = 4
line_bisection_skip = 4

fingertappingTotal = 177
FFLTotal = 184
SVGTotal = 173
line_bisection_total = 179

def subjectinfoFFL(subject_id):
    output = []
    names = ['Finger', 'Foot', 'Lips']
    onsets = [range(4 - FFLSkip, FFLTotal - FFLSkip, 6 * 6),
              range(4 + 12 - FFLSkip, FFLTotal - FFLSkip, 6 * 6),
              range(4 + 24 - FFLSkip, FFLTotal - FFLSkip, 6 * 6)]
    output.insert(0,
                      Bunch(conditions=names,
                            onsets=deepcopy(onsets),
                            durations=[[6], [6], [6]],
                            amplitudes=None,
                            tmod=None,
                            pmod=None,
                            regressor_names=None,
                            regressors=None))
    return output

def subjectinfoFingertapping(subject_id):
    output = []
    names = ['Task']
    onsets = [range(10 - fingertappingSkip, fingertappingTotal - fingertappingSkip, 2 * 12)]
    output.insert(0,
                      Bunch(conditions=names,
                            onsets=deepcopy(onsets),
                            durations=[[12]],
                            amplitudes=None,
                            tmod=None,
                            pmod=None,
                            regressor_names=None,
                            regressors=None))
    return output

def subjectinfoSVG(subject_id):
    output = []
    names = ['Task']
    onsets = [range(4 - SVGSkip, SVGTotal - SVGSkip, 2 * 12)]#[range(4 - SVGSkip, SVGTotal - SVGSkip, 2 * 12)]
    output.insert(0,
                      Bunch(conditions=names,
                            onsets=deepcopy(onsets),
                            durations=[[12]],
                            amplitudes=None,
                            tmod=None,
                            pmod=None,
                            regressor_names=None,
                            regressors=None))
    return output

def subjectinfoLineBisection(subject_id):
    output = []
    names = ['Task']
    onsets = [range(10 - line_bisection_skip, line_bisection_total - line_bisection_skip, 2 * 12)]#[range(4 - SVGSkip, SVGTotal - SVGSkip, 2 * 12)]
    output.insert(0,
                      Bunch(conditions=names,
                            onsets=deepcopy(onsets),
                            durations=[[12]],
                            amplitudes=None,
                            tmod=None,
                            pmod=None,
                            regressor_names=None,
                            regressors=None))
    return output


cont1 = ['Task>Rest', 'T', ['Task'], [1]]
contrasts_single_task = [cont1]

contFFL1 = ['Finger-Rest', 'T', ['Finger', 'Foot','Lips'], [2, -1, -1]]
contFFL2 = ['Lips-Rest', 'T', ['Finger', 'Foot','Lips'], [-1, 2, -1]]
contFFL3 = ['Foot-Rest', 'T', ['Finger', 'Foot','Lips'], [-1, -1, 2]]
contFFL4 = ['Finger>Rest', 'T', ['Finger'], [1]]
contFFL5 = ['Lips>Rest', 'T', ['Foot'], [1]]
contFFL6 = ['Foot>Rest', 'T', ['Lips'], [1]]
contrastsFFL = [contFFL1, contFFL2, contFFL3, contFFL4, contFFL5, contFFL6]


l1pipeline = pe.Pipeline()
l1pipeline.config['workdir'] = os.path.abspath('../workingdir')
l1pipeline.config['use_parameterized_dirs'] = True

l1pipeline.connect([(datasource, skullstrip, [('struct', 'infile')]),
                  ])

masks = {}
                                             
masks['fingerTapping'] = [nw.NodeWrapper(misc.PickAtlas(labels=1024,
                                             dilation_size=0), 
                                             diskbased=True, 
                                             name= "left_precentral_gyrus_mask"),
                          nw.NodeWrapper(misc.PickAtlas(labels=2024,
                                             dilation_size=0),
                                             diskbased=True,
                                             name= "right_precentral_gyrus_mask")]
masks['silentVerb'] = [nw.NodeWrapper(misc.PickAtlas(labels=[1018,1020],
                                             dilation_size=0), 
                                             diskbased=True, 
                                             name= "left_parsopercularis_and_pars_triangularis_mask"),
                          nw.NodeWrapper(misc.PickAtlas(labels=[2018,2020],
                                             dilation_size=0),
                                             diskbased=True,
                                             name= "right_parsopercularis_and_pars_triangularis_mask")]
maskInterfaces = {}
for k,v in masks.iteritems():
    maskInterfaces[k] = []
    for mask in v:
        l1pipeline.connect([(datasource, mask, [('segmentation', 'atlas')])])
        maskInterfaces[k].append({"object":mask, "outputFile":'mask_file'})
          
    maskInterfaces[k].append({"object":skullstrip, "outputFile":'outfile'})

import nifti as ni
def getVoxDims(volume):
    nii = ni.NiftiImage(volume)
    voxdims = nii.getVoxDims()
    return [voxdims[0], voxdims[1], voxdims[2]]

#for k, v in masks.items():
#    coregisteredReslicedMasksInt[k] = []
#    for mask in v:
#        normalizeAtlasToStruct = nw.NodeWrapper(interface=spm.Normalize(), diskbased=True, name="NormalizeAtlasToStruct" + mask.name.replace(os.sep, "_") + ".spm")
#        normalizeAtlasToStruct.inputs.jobtype = 'write'
#        l1pipeline.connect([(segment, normalizeAtlasToStruct , [('inverse_transformation_mat', 'parameter_file')]),
#                            (datasource, normalizeAtlasToStruct, [(('struct',getVoxDims),'write_voxel_sizes')]),
#                            (mask, normalizeAtlasToStruct, [('mask_file','apply_to_files')])])
#
#        coregisterResliceAtlas = nw.NodeWrapper(interface=spm.Coregister(), diskbased=True, name="CoregisterResliceAtlas" + mask.name.replace(os.sep, "_") + ".spm")
#        coregisterResliceAtlas.inputs.jobtype = 'write'
#        l1pipeline.connect([(datasource, coregisterResliceAtlas, [('struct', 'target')]),
#                          (normalizeAtlasToStruct, coregisterResliceAtlas, [('normalized_files', 'source')])])
#        coregisteredReslicedMasksInt[k].append({"name":coregisterResliceAtlas, "outputFile":'coregistered_files'})
#
#for v in [os.path.abspath('../masks/ctx_lh_precentral.nii'), os.path.abspath('../masks/ctx_rh_precentral.nii')]:
#	coregisteredReslicedMasksInt['fingerTapping'].append({"name":None, "outputFile":v})
    
datasink = nw.NodeWrapper(interface=nio.DataSink(),diskbased=False)
datasink.inputs.subject_directory = os.path.abspath('../output')
l1pipeline.connect([(datasource,datasink,[('subject_id','subject_id')])])

functional_nodes(pipeline=l1pipeline,
                 prefix="finger_tapping",
                 skip_vols=fingertappingSkip,
                 total_vols=fingertappingTotal,
                 datasource=datasource,
                 funcRunName='finger_tapping_func',
                 subjectinfo=subjectinfoFingertapping,
                 maskInterfaces=maskInterfaces['fingerTapping'],
                 contrasts=contrasts_single_task, datasink=datasink
                 )

functional_nodes(pipeline=l1pipeline,
                 prefix='finger_foot_lips',
                 skip_vols=FFLSkip,
                 total_vols=FFLTotal,
                 datasource=datasource,
                 funcRunName='finger_foot_lips_func',
                 subjectinfo=subjectinfoFFL,
                 maskInterfaces=maskInterfaces['fingerTapping'],
                 contrasts=contrastsFFL, datasink=datasink
                 )

functional_nodes(pipeline=l1pipeline,
                 prefix='silent_verb',
                 skip_vols=SVGSkip,
                 total_vols=SVGTotal,
                 datasource=datasource,
                 funcRunName='silent_verb_generation',
                 subjectinfo=subjectinfoSVG,
                 maskInterfaces=maskInterfaces['silentVerb'],
                 contrasts=contrasts_single_task, datasink=datasink
                 )

functional_nodes(pipeline=l1pipeline,
                 prefix='line_bisection',
                 skip_vols=line_bisection_skip,
                 total_vols=line_bisection_total,
                 datasource=datasource,
                 funcRunName='line_bisection',
                 subjectinfo=subjectinfoLineBisection,
                 maskInterfaces=maskInterfaces['fingerTapping'],
                 contrasts=contrasts_single_task, datasink=datasink
                 )
#
#######################################################################
## Setup storage of results
#
#"""
#   b. Use :class:`nipype.interfaces.io.DataSink` to store selected
#   outputs from the pipeline in a specific location. This allows the
#   user to selectively choose important output bits from the analysis
#   and keep them.
#
#   The first step is to create a datasink node and then to connect
#   outputs from the modules above to storage locations. These take the
#   following form directory_name[.[@]subdir] where parts between []
#   are optional. For example 'realign.@mean' below creates a
#   directory called realign in 'l1output/subject_id/' and stores the
#   mean image output from the Realign process in the realign
#   directory. If the @ is left out, then a sub-directory with the name
#   'mean' would be created and the mean image would be copied to that
#   directory. 
#"""
#datasink = nw.NodeWrapper(interface=nio.DataSink(), diskbased=False)
#datasink.inputs.subject_directory = os.path.abspath('../spm/l1output')
#
## store relevant outputs from various stages of the 1st level analysis
#l1pipeline.connect([(datasource, datasink, [('subject_id', 'subject_id')]),
#                    (contrastestimate, datasink, [('con_images', 'contrasts.@con'),
#                                                  ('spmT_images','contrasts.@T'),
#                                                ('parameterization','parameterization')]),
#                    
#                    ])

##########################################################################
# Execute the pipeline
##########################################################################

"""
   The code discussed above sets up all the necessary data structures
   with appropriate parameters and the connectivity between the
   processes, but does not generate any output. To actually run the
   analysis on the data the ``nipype.pipeline.engine.Pipeline.Run``
   function needs to be called. 
"""
if __name__ == '__main__':
    l1pipeline.export_graph(show=True, use_execgraph=True)
    l1pipeline.run()
#    l2pipeline.run()


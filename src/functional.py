import nipype.interfaces.io as no           # Data i/o 
import nipype.interfaces.spm as spm          # spm
import nipype.interfaces.freesurfer as fs    # freesurfer
import nipype.pipeline.node_wrapper as nw    # nodes for pypelines
import nipype.pipeline.engine as pe          # pypeline engine
import nipype.algorithms.rapidart as ra      # artifact detection
import nipype.algorithms.modelgen as model   # model specification
import os                                    # system functions


def makelist(item):
    return [item]

def functional_nodes(prefix, skip_vols, total_vols, pipeline, datasource, funcRunName,
                     subjectinfo, contrasts, maskInterfaces, datasink):
    skip = nw.NodeWrapper(interface=fsl.ExtractRoi(), diskbased=True, name=prefix + "_Skip.fsl")
    skip.inputs.tmin = skip_vols
    skip.inputs.tsize = total_vols

    realign = nw.NodeWrapper(interface=spm.Realign(), diskbased=True, name=prefix + "_Realign.spm")
    realign.inputs.register_to_mean = True

    split = nw.NodeWrapper(interface=fsl.Split(), diskbased=True, name=prefix + "_Split.fsl")
    split.inputdimension = 't'

    coregister = nw.NodeWrapper(interface=spm.Coregister(), diskbased=True, name=prefix + "_CoregisterFuncToStruct.spm")
    coregister.inputs.jobtype = 'estwrite'

    smooth = nw.NodeWrapper(interface=spm.Smooth(), diskbased=True, name=prefix + "_Smooth.spm")
    smooth.inputs.fwhm = [2, 2, 2]
    fs.FSInfo.subjectsdir('/home/filo/data/fs/')
    surfregister = nw.NodeWrapper(interface=fs.BBRegister(), diskbased=True, name=prefix + "_SurfReg.spm")
    surfregister.inputs.contrast_type = 't2'
    surfregister.inputs.init_reg = 'header'
    
#    smooth = nw.NodeWrapper(interface=fs.Smooth(), diskbased=True, name=prefix + "_Smooth.spm")
#    smooth.inputs.surface_fwhm = 2
#    smooth.inputs.vol_fwhm     = 2
#    smooth.iterfield = ['sourcefile']

    modelspec = nw.NodeWrapper(interface=model.SpecifyModel(), diskbased=True, name=prefix + "_Model")
    modelspec.inputs.input_units = 'scans'
    modelspec.inputs.output_units = 'scans'
    modelspec.inputs.time_repetition = 2.5
    modelspec.inputs.high_pass_filter_cutoff = 128

    pipeline.connect([(datasource, skip, [(funcRunName, 'infile')]),
                      (skip, realign, [('outfile', 'infile')]),
                      (realign, split, [('realigned_files', 'infile')]),
                      (realign, coregister, [('mean_image', 'source')]),
                      (split, coregister, [('outfiles', 'apply_to_files')]),
                      (datasource, coregister, [('struct', 'target')]),
                      (coregister, surfregister, [('coregistered_source', 'sourcefile')]),
                      (datasource, surfregister, [('subject_id','subject_id')]),
#                      (surfregister, smooth, [('outregfile','regfile')]),
                      (coregister, smooth, [('coregistered_files', 'infile')]),
                      (datasource, modelspec, [('subject_id', 'subject_id'),
                                               (('subject_id', subjectinfo), 'subject_info')]),
                      (realign, modelspec, [('realignment_parameters', 'realignment_parameters')]),
                      (smooth, modelspec, [(('smoothed_files', makelist), 'functional_runs')])
                      ])

    for maskInterface in maskInterfaces:
    	if maskInterface["object"] is None:
    		name = maskInterface["outputFile"].replace(os.sep, "_")
    	else:
    		name = maskInterface["object"].name

        level1design = nw.NodeWrapper(interface=spm.Level1Design(), diskbased=True, name=prefix + "_Level1Design" + name + ".spm")
        level1design.inputs.timing_units = modelspec.inputs.output_units
        level1design.inputs.interscan_interval = modelspec.inputs.time_repetition
        level1design.inputs.bases = {'hrf':{'derivs': [0, 0]}}
    	if maskInterface["object"] is None:
    		level1design.inputs.mask_image = maskInterface["outputFile"]
    		pipeline.connect([(modelspec, level1design, [('session_info', 'session_info')])])
    	else:
        	pipeline.connect([(modelspec, level1design, [('session_info', 'session_info')]),
                            (maskInterface["object"], level1design, [(maskInterface["outputFile"], 'mask_image')])])

        level1estimate = nw.NodeWrapper(interface=spm.EstimateModel(), diskbased=True, name=prefix + "_EstimateModel" + name + ".spm")
        level1estimate.inputs.estimation_method = {'Classical' : 1}
        contrastestimate = nw.NodeWrapper(interface=spm.EstimateContrast(), diskbased=True, name=prefix + "_EstimateContrast" + name + ".spm")
        contrastestimate.inputs.contrasts = contrasts
        pipeline.connect([(level1design, level1estimate, [('spm_mat_file', 'spm_design_file')]),
                          (level1estimate, contrastestimate, [('spm_mat_file', 'spm_mat_file'),
                                                              ('beta_images', 'beta_images'),
                                                              ('residual_image', 'residual_image'),
                                                              ('RPVimage', 'RPVimage')]),
                          (contrastestimate, datasink, [('spmT_images', 'contrasts.' + prefix + name.replace(".", "_"))])])

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script for clustering metagenomic contigs based on sequence composition and
correlation between many samples."""
import sys
import pandas as pd # Used by _get_coverage
import numpy as np

from Bio import SeqIO

from probin.binning.clustering import cluster
from probin.output import Output
from probin.parser import main_parser
from probin.preprocess import main_preprocess


def main(cluster_func,contigs,p,K,epsilon,iterations,runs,verbose,serial, **kwargs):
    (clusters,clust_prob, responsibility, probability_parameters) = cluster(cluster_func, contigs, p, K, epsilon, iterations, runs, verbose, serial, **kwargs)
    return (clusters,clust_prob,responsibility, probability_parameters)

def _get_from_feature_csv(read_file):
    df = pd.read_csv(read_file,index_col=0)
    return np.array(df.values), np.array(df.index)

def _get_contigs(arg_file,kmer):
    from probin.dna import DNA
    DNA.generate_kmer_hash(kmer)
    try:
        with open(arg_file) as handle:
            seqs = list(SeqIO.parse(handle,"fasta"))
    except IOError as error:    
        print >> sys.stderr, "Error reading file %s, message: %s" % (error.filename,error.message)
        sys.exit(-1)
    except Exception as error:
        print >> sys.stderr, "Error reading file %s, message: %s" % (error.filename,error.message)
        sys.exit(-1)

    contigs = [DNA(x.id, x.seq.tostring().upper(), calc_sign=True) for x in seqs]
    composition = np.zeros((len(contigs),DNA.kmer_hash_count))
    ids = []
    for i,contig in enumerate(contigs):
        composition[i] = np.fromiter(contig.pseudo_counts,dtype=np.int) - 1
        ids.append(contig.id)
    del contigs
    return composition,np.array(ids)
    
def _get_coverage(arg_file,first_data,last_data,read_length,read_mappings=False):
    try:
        if not read_mappings:
            df = pd.io.parsers.read_table(arg_file,sep='\t',index_col=0)
            v = df.ix[:,first_data:last_data].values
            return np.log(0.1+v),np.array(df.index)
        else:
            df = pd.io.parsers.read_table(arg_file,sep='\t',index_col=0)
            v = df.ix[:,first_data:last_data].values
            from probin.model.coverage.log_coverage import read_mappings_to_log_coverage
            return read_mappings_to_log_coverage(v,df.contig_length.values.reshape(-1,1),read_length), np.array(df.index)

    except Exception as error:
        print >> sys.stderr, "Error reading file %s, message: %s" % (error.filename,error.message)
        sys.exit(-1)

if __name__=="__main__":
    parser = main_parser()
    args = parser.parse_args()
    
    params = {}
    
    #=============================
    #Execute clustering    
    #=============================
    if args.script == 'probin':
        #=============================
        #Import model and prep data for that
        #=============================
        try:
            model = __import__("probin.model.{0}.{1}".format(args.model_type,args.model),globals(),locals(),["*"],-1)
            #clustering method            
            if args.algorithm == "em":
                cluster_func = model.em
            elif args.algorithm == "kmeans":
                cluster_func = model.kmeans
            #centroids
            p = args.centroids
            #data type
            if args.model_type == "composition":
                if args.feature_vectors:
                    contigs,idx =_get_from_feature_csv(args.composition_file)
                else:
                    contigs,idx = _get_contigs(args.composition_file,args.kmer)
                outfile = args.composition_file
            elif args.model_type == "coverage":
                if args.feature_vectors:
                    contigs,idx =_get_from_feature_csv(args.coverage_file)
                else:
                    contigs,idx = _get_coverage(args.coverage_file,args.first_data,args.last_data,args.read_length,read_mappings=args.read_mappings)
                params["read_length"] = args.read_length
                outfile = args.coverage_file
            elif args.model_type == "combined":
                contigs,idxcon = _get_contigs(args.composition_file,args.kmer)
                coverage,idxcov = _get_coverage(args.coverage_file,args.first_data,args.last_data)
                contigs = np.hstack(contigs,coverage)
                params["first_data"] = args.first_data
                params["last_data"] = args.last_data
                params["read_length"] = args.read_length
                outfile = "_".join([args.composition_file,args.coverage_file])
        except ImportError:
            print "Failed to load module {0}.{1}. Will now exit".format(args.model_type,args.model)
            sys.exit(-1)

        #=============================
        #Prep output settings
        #=============================
        #TODO: Needs to be fixed to allow only coverage etc.
        Output.set_output_path(outfile,args)

        #=============================
        #Calling clustering
        #=============================
        (clusters,clust_prob,responsibilities, probability_parameters) = main(cluster_func, contigs, p, args.cluster_count,args.epsilon,args.iterations, \
                                               args.runs,args.verbose,args.serial, **params)

        
        #=============================
        #Printing Results
        #=============================
        Output.write_clustering_result(clusters,clust_prob,responsibilities, probability_parameters,idx,args)

    #=============================
    #Preprocess timeseries data for coverage
    #=============================
    elif args.script == 'preprocess':
        if args.output:
            args.output = open(args.output,'w+')
        else:
            args.output = sys.stdout
        if not args.contigs:
            print "Contigs file not correctly supplied, will now exit"
            sys.exit(-1)
        main_preprocess(args)
    else:
        pass


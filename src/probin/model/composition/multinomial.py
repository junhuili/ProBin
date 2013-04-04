#!/usr/bin/env python
"""Implementation of a multinomial model based on sequence composition"""
from scipy.special import gammaln
import numpy as np
from collections import Counter

def fit_parameters(dna_l):
    sig = Counter()
    [sig.update(part.signature) for part in dna_l]
    par = np.zeros(dna_l[0].kmer_hash_count)
    for key,cnt in sig.iteritems():
        par[key] += cnt
    par /= np.sum(par)
    return par

def fit_nonzero_parameters(dna_l):
    pseudo_sig = np.ones(dna_l[0].kmer_hash_count)
    sig = Counter()
    [sig.update(part.signature) for part in dna_l]
    for key,cnt in sig.iteritems():
        pseudo_sig[key] += cnt
    pseudo_sig /= np.sum(pseudo_sig)
    return pseudo_sig

def log_probability(signature, prob_vector):
    signature_vector = np.zeros(np.shape(prob_vector))

    for key,value in signature.iteritems():
        signature_vector[key] = value

    return np.sum((signature_vector * np.log(prob_vector)) - _log_fac(signature_vector)) + _log_fac(np.sum(signature_vector))

def _log_fac(i):
    # gammaln produces the natural logarithm of the factorial of i-1
    return gammaln(i+1)

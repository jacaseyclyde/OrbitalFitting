#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This module implements the probability functions used by MCMC.
# Copyright (C) 2017-2018  J. Andrew Casey-Clyde
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Created on Fri Feb  9 16:08:27 2018

@author: jacaseyclyde
"""
# pylint: disable=C0413
import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

from . import orbits  # noqa

import numpy as np  # noqa

from scipy.stats import multivariate_normal  # noqa

np.set_printoptions(precision=5, threshold=np.inf)


class Model(object):
    """Probability model for MCMC.

    This class defines the probability models used for MCMC, keeps track of the
    dataset, and sets up several constant parameters that don't vary with the
    orbital model used.

    Parameters
    ----------
    data : :obj:`numpy.ndarray`
        A numpy array of ppv data points.

        Each data point is itself a list of the form [ra, dec, vel], where ra
        and dec are the right ascension and declination, respectively, in
        radians, while vel is the recessional velocity in units of km/s, and is
        based on the moment 1 map of the original data cube, which is itself an
        intensity weighted average of the gas velocity at each sky position.
    space : :obj:`numpy.ndarray`
        A 2-d array of floats that gives the bounds of the model parameter
        space, where the first axis represents the axes of the parameter space,
        while the 2nd axis are the minimum and maximum values of the parameter
        space axes.

    Attributes
    ----------
    data : :obj:`numpy.ndarray`
        A numpy array of ppv data points. This is the same dataset that each
        `Model` object should be instantiated with.
    cov : :obj:`numpy.ndarray`
        The covariance matrix of `data`.
    inv_cov : :obj:`numpy.ndarray`
        The inverse of `cov`.

    """

    def __init__(self, data, space):
        self.data = data
        self.space = space
        self.cov = np.cov(self.data, rowvar=False)

    def model_pt_prob(self, model_pt):
        """Calculates the probability for one point to generate another.

        Calculates the probability that a data point (`data_pt`) could have
        been generated from a 3D gaussian in ppv space centered on another
        point (the `model_pt`).

        Parameters
        ----------
        data_pt : float
            The data point to calculate generation probability for.
        model_pt : float
            The model point that the gaussian is centered on.

        Returns
        -------
        float
            The probability that `data_pt` could have been generated from
            `model_pt`.

        """
        prob = multivariate_normal.pdf(self.data, mean=model_pt, cov=self.cov)

        if np.isnan(prob):
            prob = 0.0

        return prob

    def point_model_prob(self, model):
        """Calculates the probability that a data point came from a model.

        Calculates the probability that a data point (`data_pt`) could have
        been generated by the model `model`.

        Parameters
        ----------
        data_pt : float
            The data point to calculate generation probability for.
        model : :obj:`numpy.ndarray`
            The model function that is being investigated.

        Returns
        -------
        float
            The probability that `data_pt` could have been generated by any
            point in `model`.

        """
        prob = 0.  # probability of getting point d, given model E

        for model_pt in model:
            prob += self.model_pt_prob(model_pt)

        # Normalize over all the points in the model
        prob /= model.shape[0]  # num discrete model pts

        return prob

    def ln_like(self, theta):
        """Calculates the ln probability of a dataset generating from a model.

        Calculates the probability that the dataset associated with instances
        of this class could have been generated by an orbital model defined by
        the set of parameters `theta`, without any prior knowledge of the
        parameter space.

        Parameters
        ----------
        theta : :obj:`numpy.ndarray`
            An array of orbital parameters in the form::

                numpy.array([aop, loan, inc, r_per, r_ap])

            which define the orbital model to check probabilities for.

        Returns
        -------
        float
            The log likelihood that the associated dataset could have been
            generated by the given model.

        """
        model = orbits.model(theta)

        ln_like = 0.

        with np.errstate(divide='ignore'):  # suppress divide by zero warnings
            for data_pt in self.data:
                ln_like += np.log(self.point_model_prob(data_pt, model))

        return ln_like

    def ln_prior(self, theta):
        """The log likelihood of the priors.

        The log likelihood that the orbital model defined by `theta` is
        correct, based on our prior knowledge of the orbit and parameter space.

        Parameters
        ----------
        theta : :obj:`numpy.ndarray`
            An array of orbital parameters in the form::

                numpy.array([aop, loan, inc, r_per, r_ap])

            which define the orbital model being checked.

        Returns
        -------
        float
            The log likelihood that the orbital model defined by `theta` is
            correct, given our prior knowledge of the region.

        Notes
        -----
        Currently, we are assuming a flat prior within the parameter space.

        """
        prior = 1.
        for i in range(self.space.shape[0]):
            pmin = min(self.space[i])
            pmax = max(self.space[i])

            if theta[i] < pmin or theta[i] > pmax:
                prior *= 0.
            else:
                prior *= (1. / (pmax - pmin))

        with np.errstate(divide='ignore'):  # suppress divide by zero warnings
            ln_prior = np.log(prior)
        return ln_prior

    def ln_prob(self, theta):
        """Calculates the probability that a dataset generated from a model.

        Calculates the probability that the dataset associated with instances
        of this class could have been generated by an orbital model defined by
        `theta`. Accounts for any prior probability knowledge of the parameter
        space.

        Parameters
        ----------
        theta : :obj:`numpy.ndarray`
            An array of orbital parameters in the form::

                numpy.array([aop, loan, inc, r_per, r_ap])

            which define the orbital model being investigated.

        Returns
        -------
        float
            The log likelihood that the associated dataset could have been
            generated by the model defined by `theta`, given prior knowledge of
            the region.

        """
        ln_prior = self.ln_prior(theta)
        ln_like = self.ln_like(theta)
        return ln_prior + ln_like

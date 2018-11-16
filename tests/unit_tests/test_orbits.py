#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This is MCOrbit, an MCMC application for fitting orbits near Sgr A*.
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

"""Orbit tests.

Collection of tests to ensure that the orbit generation functions are
working as expected.

"""
import numpy as np
import astropy.units as u

from mcorbit import orbits


class TestPotential(object):
    def test_inf(self):
        assert orbits.potential(np.inf * u.pc) == 0

    def test_0(self):
        assert orbits.potential(0 * u.pc) == -np.inf

    def test_units(self):
        assert orbits.potential(1 * u.pc).unit == (u.pc ** 2) / (u.yr ** 2)


class TestGradient(object):
    def test_inf(self):
        assert orbits.potential_grad(np.inf * u.pc) == 0

    def test_0(self):
        assert orbits.potential_grad(0 * u.pc) == np.inf

    def test_units(self):
        assert orbits.potential_grad(1 * u.pc).unit == u.pc / (u.yr ** 2)


class TestAngularMomentum(object):
    def test_bounds(self):
        r1 = 1. + np.random.rand()
        r2 = r1 + 4. * np.random.rand()
        l_cons = orbits.angular_momentum(r1, r2).value
        lower_bound = ((r1 ** 3) * orbits.potential_grad(r1)).value
        upper_bound = ((r2 ** 3) * orbits.potential_grad(r2)).value
        assert (((l_cons ** 2) >= lower_bound)
                and ((l_cons ** 2) <= upper_bound))

    def test_units(self):
        assert orbits.angular_momentum(1., 1.5).unit == (u.pc ** 2) / u.yr

    def test_circle(self):
        r_test = 1. * u.pc
        l_mom = orbits.angular_momentum(r_test, r_test)
        assert (l_mom ** 2) / (r_test ** 3) == orbits.potential_grad(r_test)


class TestOrbit(object):
    def test_circle(self):
        r1 = 1.5
        r_pos, r_vel, ang_pos, ang_vel = orbits.orbit(r1, r1, 500 * u.yr)
        assert all(r_pos.value == r1)

    def test_ellipse(self):
        r1 = np.float128(1.) + 1.5 * np.random.rand()
        r2 = r1 + 1.5 * np.random.rand()
        r_pos, r_vel, ang_pos, ang_vel = orbits.orbit(r1, r2, 500 * u.yr)
        assert all(r_pos.value >= r1) and all(r_pos.value <= r2)
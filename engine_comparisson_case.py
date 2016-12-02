#Implements the TASOPT engine model, currently disregards BLI
import numpy as np
from gpkit import Model, Variable, SignomialsEnabled, units
from gpkit.constraints.linked import LinkedConstraintSet
from gpkit.constraints.tight import TightConstraintSet as TCS
from engine_components import FanAndLPC, CombustorCooling, Turbine, ExhaustAndThrust, OnDesignSizing, OffDesign, FanMap, LPCMap, HPCMap

#TODO
#get jet fuel Cp

class EngineOnDesign(Model):
    """
    Engine Sizing

    References:
    1. TASOPT Volume 2: Appendicies dated 31 March 2010
    (comments B.### refer to eqn numbers in TASOPT Appendix
    section B)
    2. Flight Vehicle Aerodynamics (Prof Drela's 16.110 text book)
    3. https://www.grc.nasa.gov/www/k-12/airplane/isentrop.html
    4. Prof Barret's Spring 2015 16.50 Notes

    All engine station definitions correltate to TASOPT figure B.1

    Fan efficiency is taken from TASOPT table B.1
    Compressor efficiency is taken from TASOPT table B.2
    """

    def __init__(self, **kwargs):
        #set up the overeall model for an on design solve
        m6opt = 1
        m8opt = 1
        cooling = False
        tstages = 1
        
        lpc = FanAndLPC()
        combustor = CombustorCooling(cooling)
        turbine = Turbine()
        thrust = ExhaustAndThrust()
        size = OnDesignSizing(m6opt, m8opt, cooling, tstages)

        self.submodels = [lpc, combustor, turbine, thrust, size]

        M2 = .4
        M25 = .5
        M4a = 1
        Mexit = 1
            
        with SignomialsEnabled():

            lc = LinkedConstraintSet([self.submodels])

            substitutions = {
            'T_0': 230,   #36K feet
            'P_0': 19.8,    #36K feet
            'M_0': 0.8,
            'T_{t_4}': 1400,
            '\pi_f': 1.5,
            '\pi_{lc}': 3,
            '\pi_{hc}': 10,
            '\pi_{d}': .99,
            '\pi_{fn}': .98,
            '\pi_{tn}': .99,
            '\pi_{b}': .94,
            'alpha': 8,
            'alphap1': 9,
            'M_{4a}': M4a,    #choked turbines
            'F_D': 5.751e+04, #737 max thrust in N
            'M_2': M2,
            'M_{2.5}':M25,
            'hold_{2}': 1+.5*(1.398-1)*M2**2,
            'hold_{2.5}': 1+.5*(1.354-1)*M25**2,
            'T_{ref}': 288.15,
            'P_{ref}': 101.325,

            #new subs for cooling flow losses
            'T_{t_f}': 600,
            'hold_{4a}': 1+.5*(1.313-1)*M4a**2,
            'r_{uc}': 0.5,
            'T_{m_TO}': 1000,
            'M_{t_exit}': Mexit,
            'chold_2': (1+.5*(1.318-1)*Mexit**2)**-1,
            'chold_3': (1+.5*(1.318-1)*Mexit**2)**-2,
            'T_{t_4TO}': 1600,
            '\alpca_c': .5
            }

            #temporary objective is to minimize the core mass flux 
            Model.__init__(self, thrust.cost, lc, substitutions)

class EngineOffDesign(Model):
    """
    Engine Sizing for off design operation

    References:
    1. TASOPT Volume 2: Appendicies dated 31 March 2010
    (comments B.### refer to eqn numbers in TASOPT Appendix
    section B)
    2. Flight Vehicle Aerodynamics (Prof Drela's 16.110 text book)
    3. https://www.grc.nasa.gov/www/k-12/airplane/isentrop.html
    4. Prof Barret's Spring 2015 16.50 Notes

    All engine station definitions correltate to TASOPT figure B.1

    Fan efficiency is taken from TASOPT table B.1
    Compressor efficiency is taken from TASOPT table B.2

    Off design model takes fan pressure ratio, LPC pressure ratio,
    HPC pressure ratio, fan corrected mass flow, LPC corrected mass flow,
    HPC corrected mass flow, Tt4, and Pt5 as uknowns that are solved for
    """
    def __init__(self, sol):
        cooling = False
        
        lpc = FanAndLPC()
        combustor = CombustorCooling(cooling)
        turbine = Turbine()
        thrust = ExhaustAndThrust()
        fanmap = FanMap()
        lpcmap = LPCMap()
        hpcmap = HPCMap()

        res7 = 1
        m5opt = 0
        m7opt = 1
        
        offD = OffDesign(res7, m5opt, m7opt)

        #only add the HPCmap if residual 7 specifies a thrust
        if res7 ==0:
            self.submodels = [lpc, combustor, turbine, thrust, offD, fanmap, lpcmap]
        else:
            self.submodels = [lpc, combustor, turbine, thrust, offD, fanmap, lpcmap]
            
        with SignomialsEnabled():

            lc = LinkedConstraintSet([self.submodels])

            substitutions = {
                'T_0': sol('T_0'),   #36K feet
                'P_0': sol('P_0'),    #36K feet
                'M_0': sol('M_0'),
                
                '\pi_{tn}': sol('\pi_{tn}'),
                '\pi_{b}': sol('\pi_{b}'),
                '\pi_{d}': sol('\pi_{d}'),
                '\pi_{fn}': sol('\pi_{fn}'),
                
                'A_5': sol('A_5'),
                'A_7': sol('A_7'),
                'T_{ref}': 288.15,
                'P_{ref}': 101.325,
                'm_{htD}': sol('m_{htD}'),
                'm_{ltD}': sol('m_{ltD}'),
                
                'G_f': 1,
                'alpha': sol('alpha'),
                'alphap1': sol('alphap1'),
                
                'F_{spec}': 4.881e+04 ,
                'T_{t_{4spec}}': 1600,
                
                'm_{fan_D}': sol('alpha')*sol('m_{core}'),
                'N_{{bar}_Df}': 1,
                '\pi_{f_D}': sol('\pi_f'),
                'm_{core_D}': sol('m_{core}'),
                '\pi_{lc_D}': sol('\pi_{lc}'),
                'm_{lc_D}': sol('m_{lc_D}'),
                'm_{fan_bar_D}': sol('m_{fan_bar_D}'),
                'm_{hc_D}': sol('m_{hc_D}'),
                '\pi_{hc_D}': sol('\pi_{hc}'),

                'T_{t_f}': sol('T_{t_f}'),
            }
        if cooling == True:
            substitutions.update({
                'M_{4a}': .6,#sol('M_{4a}'),
                'hold_{4a}': 1+.5*(1.313-1)*.6**2,#sol('hold_{4a}'),
                'r_{uc}': 0.5,
                '\alpca_c': .5,

                
                'T_{m_TO}': 1000,
                'M_{t_exit}': .6,
                'chold_2': (1+.5*(1.318-1)*.6**2)**-1,
                'chold_3': (1+.5*(1.318-1)*.6**2)**-2,
                'T_{t_4TO}': 1600,
                })
        
        Model.__init__(self, thrust.cost, lc, substitutions)
   
if __name__ == "__main__":
    engineOnD = EngineOnDesign()
    
    solOn = engineOnD.localsolve(verbosity = 4, solver="mosek")
    
    engineOffD = EngineOffDesign(solOn)
    
    solOff = engineOffD.localsolve(verbosity = 4, solver="mosek",iteration_limit=200)
    print solOff('F')

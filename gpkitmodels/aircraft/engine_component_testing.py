from gpkit import Model, Variable, SignomialsEnabled, units
from gpkit.constraints.linked import LinkedConstraintSet
from gpkit.constraints.tight import TightConstraintSet as TCS
from engine_components import FanAndLPC, CombustorCooling, Turbine, ExhaustAndThrust, OnDesignSizing, CompressorMap, OffDesign
from engine import EngineOnDesign

if __name__ == "__main__":
    fan = FanAndLPC()
    fan.substitutions.update({
            'T_0': 216.5,   #36K feet
            'P_0': 22.8,    #36K feet
            'M_0': 0.8,
            '\pi_f': 1.5,
            '\pi_{lc}': 3,
            '\pi_{hc}': 10,
            '\pi_{d}': 1,
            '\pi_{fn}': 1
            })
    fansol = fan.solve(verbosity = 0)

    combustor = CombustorCooling()
    combustor.substitutions.update({
        'T_{t_4}': 1400,
        '\pi_{b}': 1,
        'h_{t_3}': fansol('h_{t_3}'),
        'P_{t_3}': fansol('P_{t_3}')
        })
    combsol = combustor.localsolve(verbosity = 0)
##    print ["constraint1", combsol('h_{t_4.1}')-(fansol('h_{t_3}')-fansol('h_{t_2.5}'))/(1+combsol('f'))]
##    print combsol('h_{t_4.1}')
##    print ["constraint 2 RHS",-(fansol('h_{t_2.5}')-fansol('h_{t_1.8}')+10*(fansol('h_{t_2.1}')-fansol('h_{t_2}')))]
##    print combsol('P_{t_4.1}')
##    print combsol('f')
##    print combsol('T_{t_4.1}')
    
##    turbine = Turbine()
##    turbine.substitutions.update({
##        'alpha': 10,
##        'h_{t_3}': fansol('h_{t_3}'),
##        'h_{t_2.5}': fansol('h_{t_2.5}'),
##        'h_{t_1.8}': fansol('h_{t_1.8}'),
##        'h_{t_2.1}': fansol('h_{t_2.1}'),
##        'h_{t_2}': fansol('h_{t_2}'),
##        'h_{t_4.1}': combsol('h_{t_4.1}'),
##        'P_{t_4.1}': combsol('P_{t_4.1}'),
##        '\pi_{tn}': 1,
##        #'h_{t_4.5}': 1093420.94025,
##        'f': combsol('f'),
##        'T_{t_4.1}': combsol('T_{t_4.1}')
##        })
##    #turbinesol = turbine.solve()
##    turbinesol = turbine.solve(verbosity = 0)
    
    exhaust = ExhaustAndThrust()
    exhaust.substitutions.update({
        'a_0': fansol('a_0'),
        'u_0': fansol('u_0'),
        'T_0': 216.5,   #36K feet
        'P_0': 22.8,    #36K feet
        'M_0': 0.8,
        'alpha': 10,
        'alphap1': 11,
        'M_{4a}': 1,    #choked turbines
        'P_{t_7}': fansol('P_{t_7}'),
        'T_{t_7}': fansol('T_{t_7}'),
        'h_{t_7}': fansol('h_{t_7}'),
        'P_{t_5}': 1006.5,
        'T_{t_5}': 836.53,
        'h_{t_5}': 893420.94025,
        'm_{core}': 40,
        'f': .016
        })

    exhaustsol = exhaust.localsolve(verbosity = 0)

    #below won't solve because the model is all equality constraints
    #so feasible region is a single point
##    design = OnDesignSizing()
##    design.substitutions.update({
##        'a_0': fansol('a_0'),
##        'alphap1': 11,
##        'F_D': 121436.45, #737 max thrust in N
##        'M_2': .4,
##        'M_{2.5}': .5,
##        'u_8': 600,
##        'u_6': 625,
##        'T_{t_2}': fansol('T_{t_2}'),
##        'T_6': 700,
##        'T_8': 500,
##        'T_{t_2.5}': fansol('T_{t_2.5}'),
##        'P_{t_2}': fansol('P_{t_2}'),
##        'P_{t_2.5}': fansol('P_{t_2.5}'),
##        'F_{sp}': 1,
##        'hold_{2}': 1.032,
##        'hold_{2.5}': 1.05,
##        'T_{t_4.1}': combsol('T_{t_4.1}'),
##        'T_{t_4.5}': combsol('T_{t_4.1}')-200*units('K'),
##        'P_{t_4.5}': combsol('P_{t_4.1}')/3,
##        'P_{t_4.1}': combsol('P_{t_4.1}'),
##        'P_{ref}': 22,
##        'T_{ref}': 290,
##        'f': .016
##        })

##    designsol = design.solve(verbosity = 4)

    #creating a compressor map model for a HPC
##    compmap = CompressorMap(0)
##    compmap.substitutions.update({
##        'T_{ref}': 1000,
##        'T_t': 1250,
##        'm_{dot}': 38,
##        'm_D': 40,
##        'P_{ref}': 22,
##        'P_t': 25,
##        '\pi_D': 20,
##        '\pi': 21,
##        'N_{{bar}_D}': 1,
##        'N': 12,
##        '\eta_{{pol}_D}': 0.9
##        })
##    compmap.localsolve(kktsolver="ldl", verbosity = 4)

    #run the off design model
    engineOnD = EngineOnDesign()
    
    sol = engineOnD.localsolve(verbosity = 0, kktsolver="ldl")
    
    offdesign = OffDesign()
    offdesign.substitutions.update({
        'T_0': sol('T_0'),   #36K feet
        'P_0': sol('P_0'),    #36K feet
        'M_0': sol('M_0'),
        '\pi_{tn}': sol('\pi_{tn}'),
        'A_5': 1,
        'A_7': 3,
        'P_{t_4.1}': sol('P_{t_4.1}'),
        'P_{t_2.5}': sol('P_{t_2.5}'),
        'P_{t_4.5}': sol('P_{t_4.5}'),
        'T_{t_4.1}': sol('T_{t_4.1}'),
        'T_{t_4.5}': sol('T_{t_4.5}'),
        'h_{t_7}': sol('h_{t_7}'),
        'h_{t_5}': sol('h_{t_5}'),
        'P_{t_5}': sol('P_{t_5}'),
        'T_{t_1.8}': sol('T_{t_1.8}'),
        'P_{t_1.8}': sol('P_{t_1.8}'),
        'T_{ref}': 1000,
        'P_{ref}': 22,
        'm_{htD}': 2.2917277822,
        'm_{ltD}': (1+sol('f'))*sol('m_{core}')*((sol('T_{t_4.5}')/(1000*units('K')))**.5)/(sol('P_{t_4.5}')/(22*units('kPa'))),
        'f': sol('f'),
        'N_1': 1,
        'G_f': 1,
        'T_{t_2.5}': sol('T_{t_2.5}'),
        'T_7': 200,
        'T_5': 500,
        'P_{t_2}': sol('P_{t_2}'),
        'T_{t_2}': sol('T_{t_2}'),
        'T_{t_{4spec}}': 1400
        })

    sol = offdesign.solve(verbosity = 0)
    print sol.table()

#
# Lead acid base model class
#

import pybamm
import os


class BaseModel(pybamm.BaseBatteryModel):
    """
    Overwrites default parameters from Base Model with default parameters for
    lead-acid models


    **Extends:** :class:`pybamm.BaseBatteryModel`

    """

    def __init__(self, options=None):
        super().__init__(options)
        self.param = pybamm.standard_parameters_lead_acid

    @property
    def default_parameter_values(self):
        input_path = os.path.join(pybamm.root_dir(), "input", "parameters", "lead-acid")
        return pybamm.ParameterValues(
            "input/parameters/lead-acid/default.csv",
            {
                "Typical current [A]": 1,
                "Current function": pybamm.GetConstantCurrent(
                    pybamm.standard_parameters_lead_acid.I_typ
                ),
                "Electrolyte diffusivity": os.path.join(
                    input_path, "electrolyte_diffusivity_Gu1997.py"
                ),
                "Electrolyte conductivity": os.path.join(
                    input_path, "electrolyte_conductivity_Gu1997.py"
                ),
                "Electrolyte viscosity": os.path.join(
                    input_path, "electrolyte_viscosity_Chapman1968.py"
                ),
                "Darken thermodynamic factor": os.path.join(
                    input_path, "darken_thermodynamic_factor_Chapman1968.py"
                ),
                "Negative electrode OCV": os.path.join(
                    input_path, "lead_electrode_ocv_Bode1977.py"
                ),
                "Positive electrode OCV": os.path.join(
                    input_path, "lead_dioxide_electrode_ocv_Bode1977.py"
                ),
            },
        )

    @property
    def default_geometry(self):
        return pybamm.Geometry("1D macro")

    def set_standard_output_variables(self):
        super().set_standard_output_variables()
        # Current
        icell = pybamm.standard_parameters_lead_acid.current_density_with_time
        icell_dim = (
            pybamm.standard_parameters_lead_acid.dimensional_current_density_with_time
        )
        I = pybamm.standard_parameters_lead_acid.dimensional_current_with_time
        self.variables.update(
            {
                "Total current density": icell,
                "Total current density [A.m-2]": icell_dim,
                "Current [A]": I,
            }
        )

        # Time
        time_scale = pybamm.standard_parameters_lead_acid.tau_discharge
        self.variables.update(
            {
                "Time [s]": pybamm.t * time_scale,
                "Time [min]": pybamm.t * time_scale / 60,
                "Time [h]": pybamm.t * time_scale / 3600,
                "Discharge capacity [A.h]": I * pybamm.t * time_scale / 3600,
            }
        )

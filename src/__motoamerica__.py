from wx import App
from controlpanel import HondaECU_ControlPanel
from version import __VERSION__

rid = {
	"MotoAmerica 2019: Junior Cup": "MAJC190"
}
restrictions = {
	"CBR500R": {
		"MotoAmerica 2019: Junior Cup": {
			"Ignition": [-4,10]
		}
	}
}

if __name__ == '__main__':
	app = App(redirect=True)
	__VERSION__ = __VERSION__.split("-")
	__VERSION__[0] = __VERSION__[0] + "_MAspec"
	__VERSION__ = "-".join(__VERSION__)
	gui = HondaECU_ControlPanel(__VERSION__, nobins=True, restrictions=(rid, restrictions), force_restrictions=True)
	app.MainLoop()

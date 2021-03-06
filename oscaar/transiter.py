import numpy as np
#from sympy import mpmath
from scipy import optimize,fmin,special
#from uncertainties import ufloat,umath
from matplotlib import pyplot
import oscaar

#transiter.py --- transiter.py is a transit light curve model written by Nolan Matthews
#using analytic expressions written by Mandel & Agol (2002). The code computes the
#curve for a quadratically limb-darkened star. To convert from model parameters to
#orbital/planetary parameters, expressions from Winn (2000) are used to calculate
#the inclination angle and semi-major axis to stellar radius ratio. 

#Unofficial Copyright; transiter.py is free to be used and distributed by others. 

#Function defining a quadratic line.
def quadbline(x,a,b,c):
    return a*x**2+b*x+c

#Heaviside Step Function
def heavyside(x):
    if x < 0:
        heavyside=0.0
    elif x == 0:
        heavyside=0.5
    elif x > 0:
        heavyside=1.0
    return heavyside;

#Function that normalizes the data usiung a quadratic baseline. Points on the left
#baseline from lL to lR and after egress from rL to rR are chosen. 
def normalizedata(time,data,lL,lR,rL,rR):
    #Pick points on the left and right baseline                     
    Lbline=data[lL:lR]
    lx=range(lL,lR)
    Rbline=data[rL:rR]
    rx=range(rL,rR)
    
    dataset,x=[],[]
    for ii in range(0,np.size(Lbline)):
        dataset.append(Lbline[ii])
        x.append(lx[ii])
    for ii in range(0,np.size(Rbline)):
        dataset.append(Rbline[ii])
        x.append(rx[ii])

    fit,success=optimize.curve_fit(quadbline,xdata=np.array(x),ydata=dataset)
    a,b,c=fit[0],fit[1],fit[2]
    NormFlux=data[lL:rR]/quadbline(np.arange(lL,rR),a,b,c)
    time_days=time[lL:rR]

    #Check to see if it was normalized correctly
    plot(NormFlux)
    show()
    return NormFlux,time_days,time

#Function that fits the light-curve model to a data set, given some input parameters for the planet. 
def fittransit(NormFlux,Rp,aRstar,inc,dt,Period):
    
    b1=aRstar*np.cos(np.pi*inc/180)
    vel=2*np.pi*aRstar*dt/Period
    midtrantime=np.size(NormFlux)/2
    #gam1=0.5
    #gam2=0.3
    
    xd=np.arange(np.size(NormFlux))
    
    print "Performing Fit using input guesses of,"
    print "Rp/Rs = ",Rp
    print "a/Rs = ",aRstar
    print "inclination = ",inc
    print "Period = ",Period
    fit,success=optimize.curve_fit(transiterout,
                                   xdata=xd.astype(np.float64),
                                   ydata=NormFlux.astype(np.float64),
                                   p0=(Rp,b1,vel,midtrantime)
                                   )
    return fit,success

#Light-Curve model using input parameters, Rp=planetary/stellar radius
#ratio, b1=impact parameter, vel=planetary velocity, midtrantime=,
#Mid-Transit time. 
def transiterout(x,Rp,b1,vel,midtrantime,fitting=False):    
    p=Rp/1.0
    gam1=0.25
    gam2=0.45
    
    #Make Edit Changes
    c2=gam1+2*gam2
    c4=-gam2
    c0=1-c2-c4
    Om=c0/4+c2/6+c4/8
    
    Ing,Egr=[],[]
    Flux=np.zeros(np.size(x))
    if 0.0<b1<1.0 and  0.0<gam1<1.0 and  0.0<gam2<1.0 and gam1+gam2<1.0: #Constraints on parameters
        
        for i in x:
            
            xpos=vel*(x[i]-midtrantime)
            z=np.sqrt(xpos**2+b1**2)
            a=(z-p)**2
            b=(z+p)**2
            q=p**2-z**2
            eta2=((p**2)/2)*(p**2+2*z**2)
            
            if 1+p < z:
                Flux[i]=1
            elif 0.5+abs(p-0.5) < z <= 1+p:
            
                if i < np.size(x)/2:
                    Ing.append(i)
                elif i > np.size(x)/2:
                    Egr.append(i)
                
                k=np.sqrt((1-a)/(4*z*p))
                n2=(a-1)/a
                
                #Kk=mpmath.ellipk(k**2)
                #Ek=mpmath.ellipe(k**2)
                #Pik=mpmath.ellippi(n2,k**2)
                Kk=oscaar.transitModel.ellipk(np.sqrt(m))
                Ek=oscaar.transitModel.ellipe(np.sqrt(m))
                Pik=oscaar.transitModel.ellippi(n2,np.sqrt(m))
                K0=np.arccos((p**2+z**2-1)/(2*p*z))
                K1=np.arccos((1-p**2+z**2)/(2*z))
                
                lamE=(1/np.pi)*(p**2*K0+K1-np.sqrt((4*z**2-(1+z**2-p**2)**2)/4))
                lam1=(1/(9*np.pi*np.sqrt(p*z)))*(((1-b)*(2*b+a-3)-3*q*(b-2))*Kk+4*p*z*(z**2+7*p**2-4)*Ek-3*(q/a)*Pik) 
                eta1=(1/(2*np.pi))*(K1+2*eta2*K0-0.25*(1+5*p**2+z**2)*np.sqrt((1-a)*(b-1)))
                
                Flux[i]=1-(4*Om)**-1*((1-c2)*lamE+c2*(lam1+(2/3)*0*(p-z))-c4*eta1)
                
            elif p<=z<=1-p:
                
                lamE = p**2
                k=np.sqrt((1-a)/(4*z*p))
                #Kinv=mpmath.ellipk(1/k**2)
                #Einv=mpmath.ellipe(1/k**2)
                #Pinv=mpmath.ellippi((a-b)/a,1/k**2)
                Kinv=oscaar.transitModel.ellipk(1/k)
                Einv=oscaar.transitModel.ellipe(1/k)
                Pinv=oscaar.transitModel.ellippi((a-b)/a,1/k)
                
                lam2=(2/(9*np.pi*np.sqrt(1-a)))*((1-5*z**2+p**2+q**2)*Kinv+(1-a)*(z**2+7*p**2-4)*Einv-3*(q/a)*Pinv)
                
                Flux[i]=1-(4*Om)**-1*((1-c2)*lamE+c2*(lam2+(2/3))-c4*eta2)
        
            elif 0 <= z <= 0.5-abs(p-0.5):
                lamE = p**2
                k=((1-a)/(4*z*p))
                
                #Einv=mpmath.ellipe(1/k)
                #Kinv=mpmath.ellipk(1/k)
                #Pinv=mpmath.ellippi((a-b)/a,1/k)
                Einv=oscaar.transitModel.ellipe(1/k)
                Kinv=oscaar.transitModel.ellipk(1/k)
                Pinv=oscaar.transitModel.ellippi((a-b)/a,1/k)
                
                lam2=(2/(9*np.pi*np.sqrt(1-a)))*((1-5*z**2+p**2+q**2)*Kinv+(1-a)*(z**2+7*p**2-4)*Einv-3*(q/a)*Pinv)
                
                hh=heavyside(p-z)
                fx1=1/(4*Om)
                Flux[i]=1-fx1*((1-c2)*lamE+c2*(lam2+(2.0/3.0)*hh)-c4*eta2)

    else: #If the input parameters goes beyond a constraint
        Flux=np.zeros(np.size(x))
    if fitting==True: 
        return Flux,Ing,Egr
    else:
        return Flux


def find_nearest(array,value):
    idx = (abs(array-value)).argmin()
    return idx

#Get the values on the output fit parameters
def output_params(timedays,NormFlux,fit,success,period,ecc,arg_periapsis):
	Flux,Ing,Egr=transiterout(np.arange(0,np.size(NormFlux)),fit[0],fit[1],fit[2],fit[3],fitting=True)
	print "Converting model to orbital parameters . . . "
	
	#Get values and uncertainties from the fit
	Rp=fit[0]
	b1=fit[1]
	vel=fit[2]
	midtrantime=fit[3]
	
	#Rp=ufloat(fit[0],np.sqrt(success[0][0]))
	#b1=ufloat(fit[1],np.sqrt(success[1][1]))
	#vel=ufloat(fit[2],np.sqrt(success[2][2]))
	#midtrantime=ufloat(fit[3],np.sqrt(success[3][3]))
	#gam1=ufloat((fit[4],np.sqrt(success[4][4])))
	#gam2=ufloat((fit[5],np.sqrt(success[5][5])))
	
	P=period
	#ecc_corr=np.sqrt(1-ecc**2)/(1+ecc*umath.sin(arg_periapsis*np.pi/180.))
	Ttot=(Egr[np.size(Egr)-1]-Ing[0])*ecc_corr
	Tfull=(Egr[0]-Ing[np.size(Ing)-1])*ecc_corr
	#delta=ufloat((1-Flux[fit[3]],1-Flux[fit[3]]+sqrt(success[3][3])))
	delta=Rp**2
	dt=timedays[2]-timedays[1]
	
	#aRstar=(2*delta**0.25*P/(np.pi*dt*umath.sqrt(Ttot**2-Tfull**2)))#*umath.sqrt(1-ecc**2)/(1+ecc*sin(arg_periapsis*pi/180.))
	#bmnodel=umath.sqrt((1-(Tfull/Ttot)**2)/((1-umath.sqrt(delta))**2-(Tfull/Ttot)**2 * (1+umath.sqrt(delta))**2)) #Not too sure why this doesn't work
	#inc=(180/np.pi)*umath.acos(b1/aRstar)
	#print bmodel
	
	#poutnames=('Rp','b1','vel','midtrantime','gam1','gam2')
	#for iz in range(0,np.size(fit)):
	#	print poutnames[iz],fit[iz],np.sqrt(success[iz][iz])
		
	print "--------------------------------"
	aRstarFIT=vel*P/(dt*2*np.pi)
	#incFIT=(180/np.pi)*umath.acos(b1/aRstarFIT)
	#midtrantime_convert=midtrantime*dt*24*3600+time_days[0]
	#midtrantime_MJD=timedays[midtrantime]+54964.00111764
	#timebetween = timedays[int(midtrantime.nominal_value)+1]-timedays[int(midtrantime.nominal_value)]
	#print timebetween*dt
	#print "Midtrantime",midtrantime_convert.std_dev()#midtrantime_MJD
	print "aRstarFIT",aRstarFIT
	print "inclination",incFIT
	print "frac. rad.", Rp
	print "aRstar_mod", aRstar
	aRs=(aRstarFIT+aRstar)/2
	print "--------------------------------"
	print "Planetary Radius/Star Radius: ",Rp
	print "Inclination: ",incFIT
	print "Semi - Major Axis / Stellar Radius: ",aRs
	print "Mid-Transit Time [MJD]",
	
	pyplot.plot(timedays,NormFlux,linestyle='None',marker='.')
	pyplot.plot(timedays,transiterout(np.arange(np.size(NormFlux)),fit[0],fit[1],fit[2],fit[3]))
	pyplot.show()    
	return Flux,Rp,aRstarFIT,incFIT,aRstar,midtrantime
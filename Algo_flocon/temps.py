from hexalattice.hexalattice import *
import numpy as np
from scipy.optimize import curve_fit
from fonctions_frontieres import *
from fonctions_plot import * 
import time 

# PROGRESS BAR
import sys
def progressbar(it, prefix="", size=60, out=sys.stdout): # Python3.3+
    count = len(it)
    def show(j):
        x = int(size*j/count)
        print("{}[{}{}] {}/{}".format(prefix, "#"*x, "."*(size-x), j, count), 
                end='\r', file=out, flush=True)
    show(0)
    for i, item in enumerate(it):
        yield item
        show(i+1)
    print("\n", flush=True, file=out)

# ---------PARAMETRES--------------------

rho = 0.635     # Densite
kappa = 0.0075  # Freezing parameter
iterations = 1000 # Number of iterations  A UTILISER !
alpha = 0.4
beta = 1.6
theta = 0.025
mu = 0.015
gamma = 0.0005

N_tot = [10, 20, 40, 100]
t_tot = []
# for space in N_tot : 
#     tic=time.time_ns()
#     N = space
# ----------RESEAU -------------------

# hex_centers, _ = create_hex_grid(nx=N,          # Création du résau 
#                                  ny=N,
#                                  do_plot=False)
                                 
# x_hex_coords = hex_centers[:, 0]
# y_hex_coords = hex_centers[:, 1]

# color_vapor = np.full((N ** 2,3), [1, 0, 0]) # ROUGE pour la vapeur 
# color_ice = np.full((N ** 2,3), [0, 0, 1]) # BLEU pour la glace 
# color_quasi = np.full((N ** 2,3), [0, 1, 0]) # VERT pour quasi-liquid 

# colors_init = color_ice + color_vapor + color_quasi 

# # --------------------------- MASK INITIAL --------------------
# mask_tot = np.full((N ** 2,4), [0, 0, 0, rho])    # Mask totale a=(0 ou 1 si dans cristal) b : boundary mass (quasi-liquid)
                                    # c : cristal mass (ice) d : diffusive mass (vapor)

# if N%2 == 0 : # donc pair !
#     mask_tot[int((len(mask_tot) / 2)-N/2)] = [1, 0, 1, 0]       # On fixe au milieu une cellule gelée 
#     cell_centre_domaine = int((len(mask_tot) / 2) - N/2)
# else:
#     mask_tot[int(len(mask_tot) / 2)] = [1, 0, 1, 0]       # On fixe au milieu une cellule gelée 
#     cell_centre_domaine = int((len(mask_tot) / 2))
# ----------------------FONCTIONS ÉVOLUTION---------------------------


def freezing(mask0, N, centre, kappa) :
    ## b0, d0 = masques initiaux 
    # centre = index
    mask1 = mask0
    idxa,idxb,idxc,idxd,idxe,idxf,idxg = alentours_idx(N,centre)


    idx = [idxb,idxc,idxd,idxe,idxf,idxg]
    for i in range(len(idx)) :
        mask1[idx[i],1] = mask0[idx[i], 1] + ((1-kappa)*mask0[idx[i], 3])

        mask1[idx[i],2]= mask0[idx[i], 1] + (kappa*mask0[idx[i], 3])

        mask1[idx[i],3] = 0

    return mask1

def melting(mask0, N, centre, mu, gamma) :
    ## b0, d0 = masques initiaux 
    # centre = index
    mask1 = mask0
    idxa,idxb,idxc,idxd,idxe,idxf,idxg = alentours_idx(N,centre)


    idx = [idxb,idxc,idxd,idxe,idxf,idxg]
    for i in range(len(idx)) :
        mask1[idx[i],1] = (1-mu)*mask0[idx[i],1]

        mask1[idx[i],2]= (1-gamma)*mask0[idx[i],2]

        mask1[idx[i],3] = mask0[idx[i],3] + mu*mask0[idx[i],1] + gamma*mask0[idx[i],2]

    return mask1

def attachement(mask0, N, centre, alpha, beta, theta):

    # ne fonctionne pas sur les frontières !
    if centre%N == 0 or (centre+1)%N == 0 or centre < N or centre > N*(N-1): # les frontières sont exclues
        return mask0 # Rien ne change


    nb_voisin_cristal = prox_crystal(mask0,centre)  # Entier qui donne le nb de voisin gelé
    idx_voisins = alentours_idx(N,centre)[1:]       # idx des voisins du centre, excluant idx centre

    case = mask0[centre]

    a = case[0]
    b = case[1]
    c = case[2]
    d = case[3]



    # calcul vapeur somme voisin
    vapeur_voisin_liste = []
    for ele in idx_voisins:
        vapeur_voisin_liste.append(mask0[ele,3])

    val_somme_vapeur_voisin = sum(vapeur_voisin_liste) # la somme de la vapeur des voisin du centre

    mask1 = mask0 #initialisation
    
    if nb_voisin_cristal != 0 and a == 0 :
        #1 cas nb = 1 ou 2
        if nb_voisin_cristal == 1 or 2 :
            
            if b >= beta:
                mask1[centre,0] = 1
                mask1[centre,2] = b + c
                mask1[centre,1] = 0

        #2 cas nb = 3
        if nb_voisin_cristal == 3 :
            
            if b >= 1 or (val_somme_vapeur_voisin < theta and b > alpha):
                mask1[centre,0] = 1
                mask1[centre,2] = b + c
                mask1[centre,1] = 0
        #3 cas nb >= 4
        if nb_voisin_cristal >= 4 :
            
            mask1[centre,0] = 1
            mask1[centre,2] = b + c
            mask1[centre,1] = 0
    return mask1


    
# -----------------------UDPDATE MASK ------------------------------

for space in N_tot : 
    tic=time.time_ns()
    N = space
    tic = time.time_ns()
    hex_centers, _ = create_hex_grid(nx=N,          # Création du résau 
                                 ny=N,
                                 do_plot=False)
                                 
    x_hex_coords = hex_centers[:, 0]
    y_hex_coords = hex_centers[:, 1]
    mask_tot = np.full((N ** 2,4), [0, 0, 0, rho]) 

    if N%2 == 0 : # donc pair !
        mask_tot[int((len(mask_tot) / 2)-N/2)] = [1, 0, 1, 0]       # On fixe au milieu une cellule gelée 
        cell_centre_domaine = int((len(mask_tot) / 2) - N/2)
    else:
        mask_tot[int(len(mask_tot) / 2)] = [1, 0, 1, 0]       # On fixe au milieu une cellule gelée 
        cell_centre_domaine = int((len(mask_tot) / 2))

   
    for t in range(iterations):
    #           FREEZING
        a = np.where(mask_tot[:,0]==1)
        for ele in a[0] :
            mask_change = freezing(mask_tot, N, ele, kappa)
        mask_tot = mask_change

    #           MELTING
        a = np.where(mask_tot[:,0]==1)
        for ele in a[0] :
            mask_change = melting(mask_tot, N, ele, mu, gamma)
        mask_tot = mask_change


        #plot_total(mask_tot, color_ice, color_vapor, color_quasi, x_hex_coords, y_hex_coords, N)

        for i in range(len(mask_tot)):

            #                   ATTACHEMENT
            mask_change = attachement(mask_tot, N, i, alpha, beta, theta)
        #plot_total(mask_change, color_ice, color_vapor, color_quasi, x_hex_coords, y_hex_coords, N)

            #                  DIFFUSION
        mask_1 = np.copy(mask_change)
        for i in range(len(mask_tot)):
            
            case = mask_1[i]
            if i%N == 0 or (i+1)%N == 0 or i < N or i > N*(N-1):    
                continue   

            elif case[0]==1:
                continue

            elif prox_crystal(mask_1,i) != 0: # est a proximité du cristal, condition réfléchie
                new_value = somme_vap_voisin_cristal(mask_1, i, N) #Laplacien condition réfléchie
                mask_change[i,3] = new_value

            else:  
                ele = alentours(mask_1,i) #
                new_value = somme_vap(ele)
                mask_change[i,3] = new_value  
        mask_tot = mask_change
        
    toc = time.time_ns()
    t_tot.append((toc-tic)/1.0e9)
    print(t_tot)

def func(x, a, b):
    return a * x + b

popt, pcov = curve_fit(func, np.log10(N_tot), np.log10(t_tot))
print(popt)

plt.plot(np.log10(N_tot), np.log10(t_tot), '-o',np.log10(N_tot), func(np.log10(N_tot), popt[0], popt[1]))
plt.grid(linestyle='-')
plt.title(f'Temps de calcul pour {iterations} iterations en fonction de la taille de la grille ')
plt.xlabel('log(N)')
plt.ylabel('log(t) [s]')
plt.legend(['$t_{tot}$', f'y={np.round(popt[0], 1)} * x + {np.round(popt[1], 1)}'])
plt.show()


    







# ---------------------PLOT RESULTS------------------------------------


# # GLACE 
# ice = mask_tot[:,0]
# final_mask_ice = []
# for i in range(len(mask_tot)):
#     for j in range(3):
#         final_mask_ice.append(ice[i])

# final_mask_ice_reshaped = np.reshape(final_mask_ice, (N**2, 3))
# final_color_ice = (color_ice * final_mask_ice_reshaped) 
# # VAPEUR
# vapor = mask_tot[:,3]
# final_mask_vapor = []
# for i in range(len(mask_tot)):
#     for j in range(3):
#         final_mask_vapor.append(vapor[i])

# final_mask_vapor_reshaped = np.reshape(final_mask_vapor, (N**2, 3))
# final_color_vapor = (color_vapor * final_mask_vapor_reshaped) 


# # QUASI-LIQUIDE
# quasi_liquid = mask_tot[:,1]
# final_mask_quasi_liquid = []
# for i in range(len(mask_tot)):
#     for j in range(3):
#         final_mask_quasi_liquid.append(quasi_liquid[i])

# final_mask_quasi_liquid_reshaped = np.reshape(final_mask_quasi_liquid, (N**2, 3))
# final_color_quasi_liquid = (color_quasi * final_mask_quasi_liquid_reshaped) 



# final_colors = final_color_ice + final_color_vapor + final_color_quasi_liquid



# max = np.max(final_colors)
# final_colors = final_colors/max

# max = np.max(final_color_ice)
# final_color_ice = final_color_ice/max

# max = np.max(final_color_vapor)
# final_color_vapor = final_color_vapor/max

# max = np.max(final_color_quasi_liquid)
# final_color_quasi_liquid = final_color_quasi_liquid/max




# plot_single_lattice_custom_colors(x_hex_coords, y_hex_coords,       
#                                       face_color=final_color_quasi_liquid,
#                                       edge_color=final_color_quasi_liquid,
#                                       min_diam=1,
#                                       plotting_gap=0.0,
#                                       rotate_deg=0)

# plot_total(mask_tot, color_ice, color_vapor, color_quasi, x_hex_coords, y_hex_coords, N)

# plt.title('Mask quasi liquid')
 
# plt.show()



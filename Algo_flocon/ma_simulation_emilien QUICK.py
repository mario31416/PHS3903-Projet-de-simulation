from hexalattice.hexalattice import *
import numpy as np
from fonctions_frontieres import *
from fonctions_plot import * 
import time 
from numpy import copy

# ----------TIME----------------
start = time.time()

# ---------PARAMETRES--------------------

rho, kappa, iterations, alpha, beta, theta, mu, gamma = 0.4, 0.6, 100, 0.21, 1.69, 0.02, 0.015, 0.0001      # Densite



# ----------RESEAU -------------------
N = 10 # Taille de la grille 
hex_centers, _ = create_hex_grid(nx=N,          # Création du résau 
                                 ny=N,
                                 do_plot=False)
                                 
x_hex_coords = hex_centers[:, 0]
y_hex_coords = hex_centers[:, 1]

color_vapor = np.full((N ** 2,3), [1, 0, 0]) # ROUGE pour la vapeur 
color_ice = np.full((N ** 2,3), [0, 0, 1]) # BLEU pour la glace 
color_quasi = np.full((N ** 2,3), [0, 1, 0]) # VERT pour quasi-liquid 

colors_init = color_ice + color_vapor + color_quasi 

# --------------------------- MASK INITIAL --------------------
mask_tot = np.full((N ** 2,4), [0, 0, 0, rho])    # Mask totale a=(0 ou 1 si dans cristal) b : boundary mass (quasi-liquid)
                                    # c : cristal mass (ice) d : diffusive mass (vapor)

if N%2 == 0 : # donc pair !
    mask_tot[int((len(mask_tot) / 2)-N/2)] = [1, 0, 1, 0]       # On fixe au milieu une cellule gelée 
    cell_centre_domaine = int((len(mask_tot) / 2) - N/2)
else:
    mask_tot[int(len(mask_tot) / 2)] = [1, 0, 1, 0]       # On fixe au milieu une cellule gelée 
    cell_centre_domaine = int((len(mask_tot) / 2))
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
    
    mask1[idx,1] = [(1-mu)*mask0[i,1] for i in idx]
    mask1[idx,2] = [(1-gamma)*mask0[i,2] for i in idx]
    mask1[idx,3] = [mask0[i,3] + mu*mask0[i,1] + gamma*mask0[i,2] for i in idx]


    return mask1

def attachement(mask0, N, centre, alpha, beta, theta):

    # ne fonctionne pas sur les frontières !
    if centre%N == 0 or (centre+1)%N == 0 or centre < N or centre > N*(N-1): # les frontières sont exclues
        return mask0 # Rien ne change


    nb_voisin_cristal = prox_crystal(mask0,centre)  # Entier qui donne le nb de voisin gelé
    idx_voisins = alentours_idx(N,centre)[1:]       # idx des voisins du centre, excluant idx centre

    # # calcul vapeur somme voisin
    # vapeur_voisin_liste = []
    # for ele in idx_voisins:
    #     vapeur_voisin_liste.append(mask0[ele,3])

    vapeur_voisin_liste = [mask0[ele, 3] for ele in idx_voisins] # List comprehension 

    val_somme_vapeur_voisin = sum(vapeur_voisin_liste) # la somme de la vapeur des voisin du centre

    mask1 = mask0.copy() #initialisation
    
    if nb_voisin_cristal != 0 and mask0[centre,0] == 0 :
        #1 cas nb = 1 ou 2
        if nb_voisin_cristal == 1 or 2 :
            
            if mask0[centre,1] >= beta:
                mask1[centre,0] = 1
                mask1[centre,2] = mask0[centre,1] + mask0[centre,2]
                mask1[centre,1] = 0

        #2 cas nb = 3
        if nb_voisin_cristal == 3 :
            
            if mask0[centre,1] >= 1 or (val_somme_vapeur_voisin < theta and mask0[centre,1] > alpha):
                mask1[centre,0] = 1
                mask1[centre,2] = mask0[centre,1] + mask0[centre,2]
                mask1[centre,1] = 0
        #3 cas nb >= 4
        if nb_voisin_cristal >= 4 :
            
            mask1[centre,0] = 1
            mask1[centre,2] = mask0[centre,1] + mask0[centre,2]
            mask1[centre,1] = 0
    return mask1

# -----------------------Exclure frontière du mask-----------------
print(mask_tot,'>>>>>>>>>>>>>>>>>>>>>>>>>>>>>',len(mask_tot))
new_mask = [list(mask_tot[i]) for i in range(len(mask_tot)) if isfrontiere(i, N) != 1]
mask_tot = copy(new_mask)
print(mask_tot,'>>>>>>>>>>>>>>',len(mask_tot))

    
# -----------------------UDPDATE MASK ------------------------------



   
for t in range(iterations):

#--------------------------FREEZING--------------------------------
    a = np.where(mask_tot[:,0]==1)
    for ele in a[0] :
        mask_change = freezing(mask_tot, N, ele, kappa)
    mask_tot = mask_change
    # for ele in a[0] :
    #     mask_change = freezing(mask_tot, N, ele, kappa)


#---------------------------MELTING-----------------------------------
    a = np.where(mask_tot[:,0]==1)
    for ele in a[0] :
        mask_change = melting(mask_tot, N, ele, mu, gamma)
    mask_tot = mask_change

# ------------------------ATTACHEMENT----------------------
    mask_change = [attachement(mask_tot, N, i, alpha, beta, theta) for i in range(len(mask_tot))]

#--------------------------DIFFUSION----------------------
    mask_1 = copy(mask_change)

    #On retire le cristal de la liste à loop dessus ?
    for i in range(len(mask_tot)):

        if mask_1[i,0]==1:
            continue

        elif prox_crystal(mask_1,i) != 0: # est a proximité du cristal, condition réfléchie

            mask_change[i,3] = somme_vap_voisin_cristal(mask_1, i, N)#Laplacien condition réfléchie

        else:  

            ele = alentours(mask_1,i) #
            mask_change[i,3] = somme_vap(ele) 
    
    mask_tot = mask_change
    print(t)
    #plot_total(mask_tot, color_ice, color_vapor, color_quasi, x_hex_coords, y_hex_coords, N)







# ---------------------PLOT RESULTS------------------------------------


# GLACE 
ice = mask_tot[:,0]
final_mask_ice = []
for i in range(len(mask_tot)):
    for j in range(3):
        final_mask_ice.append(ice[i])

final_mask_ice_reshaped = np.reshape(final_mask_ice, (N**2, 3))
final_color_ice = (color_ice * final_mask_ice_reshaped) 
# VAPEUR
vapor = mask_tot[:,3]
final_mask_vapor = []
for i in range(len(mask_tot)):
    for j in range(3):
        final_mask_vapor.append(vapor[i])

final_mask_vapor_reshaped = np.reshape(final_mask_vapor, (N**2, 3))
final_color_vapor = (color_vapor * final_mask_vapor_reshaped) 


# QUASI-LIQUIDE
quasi_liquid = mask_tot[:,1]
final_mask_quasi_liquid = []
for i in range(len(mask_tot)):
    for j in range(3):
        final_mask_quasi_liquid.append(quasi_liquid[i])

final_mask_quasi_liquid_reshaped = np.reshape(final_mask_quasi_liquid, (N**2, 3))
final_color_quasi_liquid = (color_quasi * final_mask_quasi_liquid_reshaped) 



final_colors = final_color_ice + final_color_vapor + final_color_quasi_liquid



max = np.max(final_colors)
final_colors = final_colors/max

max = np.max(final_color_ice)
final_color_ice = final_color_ice/max

max = np.max(final_color_vapor)
final_color_vapor = final_color_vapor/max

max = np.max(final_color_quasi_liquid)
final_color_quasi_liquid = final_color_quasi_liquid/max


plt.figure(1)
plot_single_lattice_custom_colors(x_hex_coords, y_hex_coords,       # Plot total des 3 phases 
                                      face_color= final_colors,
                                      edge_color=final_colors,
                                      min_diam=1,
                                      plotting_gap=0.0,
                                      rotate_deg=0)
plt.title('Mask total')

# plt.figure(2)

# plot_single_lattice_custom_colors(x_hex_coords, y_hex_coords,       
#                                       face_color= final_color_ice,
#                                       edge_color=final_color_ice,
#                                       min_diam=1,
#                                       plotting_gap=0.0,
#                                       rotate_deg=0)
# plt.title('Mask glace')

# plt.figure(3)

# plot_single_lattice_custom_colors(x_hex_coords, y_hex_coords,       
#                                       face_color=final_color_vapor,
#                                       edge_color=final_color_vapor,
#                                       min_diam=1,
#                                       plotting_gap=0.0,
#                                       rotate_deg=0)

# plt.title('Mask vapeur')

# plt.figure(4)

# plot_single_lattice_custom_colors(x_hex_coords, y_hex_coords,       
#                                       face_color=final_color_quasi_liquid,
#                                       edge_color=final_color_quasi_liquid,
#                                       min_diam=1,
#                                       plotting_gap=0.0,
#                                       rotate_deg=0)

# plt.title('Mask quasi liquid')
 
end = time.time()
print(f"Runtime of the program is {end - start}")
plt.show()

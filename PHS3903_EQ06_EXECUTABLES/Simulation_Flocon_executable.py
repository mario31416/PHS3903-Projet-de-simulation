## pip install hexalattice

from hexalattice.hexalattice import *
import numpy as np
from fonctions_frontieres import *
from fonctions_plot import * 
import time 

# ----------TIME----------------

start = time.time()

# ---------PARAMETRES--------------------


rho = 0.635        # Densite
kappa = 0.0075     # Paramètre de gèle
iterations = 500  # Nombre d'itérations
alpha = 0.04       # Paramètre d'attachement
theta = 0.0125     # Paramètre d'attachement
beta = 2.2         # Paramètre d'attachement
mu = 0.015         # Paramètre de fonte
gamma = 0.0005     # Paramètre de fonte



# ----------RESEAU -------------------

N =100 # Taille du domaine 

hex_centers, _ = create_hex_grid(nx=N,          # Création du résau 
                                ny=N,
                                do_plot=False)
                                
x_hex_coords = hex_centers[:, 0]
y_hex_coords = hex_centers[:, 1]

color_vapor = np.full((N ** 2,3), [1,0, 0]) # ROUGE pour la vapeur 
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
    mask_tot[int(len(mask_tot) / 2)] = [1, 0, 1, 0]             
    cell_centre_domaine = int((len(mask_tot) / 2))


# Cristal initial en Y
# mask_tot[int((len(mask_tot) / 2)-N/2)+3*N-1] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)+N] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)+2*N-1] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)-3*N-1] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)-N] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)-2*N-1] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)+3] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)+1] = [1, 0, 1, 0]
# mask_tot[int((len(mask_tot) / 2)-N/2)+2] = [1, 0, 1, 0]


# ----------------------FONCTIONS ÉVOLUTION---------------------------


_range_mask_tot = len(mask_tot)
def freezing(mask0, N, centre, kappa) : 
    mask1 = mask0
    idxa,idxb,idxc,idxd,idxe,idxf,idxg = alentours_idx(N,centre)


    idx = [idxb,idxc,idxd,idxe,idxf,idxg]
    for i in range(len(idx)) :
        mask1[idx[i],1] = mask0[idx[i], 1] + ((1-kappa)*mask0[idx[i], 3])

        mask1[idx[i],2]= mask0[idx[i], 1] + (kappa*mask0[idx[i], 3])

        mask1[idx[i],3] = 0

    return mask1

def melting(mask0, N, centre, mu, gamma) :
    mask1 = mask0
    idxa,idxb,idxc,idxd,idxe,idxf,idxg = alentours_idx(N,centre)


    idx = [idxb,idxc,idxd,idxe,idxf,idxg]
    for i in range(len(idx)) :
        mask1[idx[i],1] = (1-mu)*mask0[idx[i],1]

        mask1[idx[i],2]= (1-gamma)*mask0[idx[i],2]

        mask1[idx[i],3] = mask0[idx[i],3] + mu*mask0[idx[i],1] + gamma*mask0[idx[i],2]

    return mask1

def attachement(mask0, N, centre, alpha, beta, theta):

    if centre%N == 0 or (centre+1)%N == 0 or centre < N or centre > N*(N-1): # les frontières sont exclues
        return mask0 


    nb_voisin_cristal = prox_crystal(mask0,centre)  
    idx_voisins = alentours_idx(N,centre)[1:]       

    vapeur_voisin_liste = [mask0[ele, 3] for ele in idx_voisins]  

    val_somme_vapeur_voisin = sum(vapeur_voisin_liste) 

    mask1 = mask0 #initialisation
    
    if nb_voisin_cristal != 0 and mask0[centre,0] == 0 :
        #1 cas nombre voisins = 1 ou 2
        if nb_voisin_cristal == 1 or 2 :
            
            if mask0[centre,1] >= beta:
                mask1[centre,0] = 1
                mask1[centre,2] = mask0[centre,1] + mask0[centre,2]
                mask1[centre,1] = 0

        #2 cas nombre voisins = 3
        if nb_voisin_cristal == 3 :
            
            if mask0[centre,1] >= 1 or (val_somme_vapeur_voisin < theta and mask0[centre,1] > alpha):
                mask1[centre,0] = 1
                mask1[centre,2] = mask0[centre,1] + mask0[centre,2]
                mask1[centre,1] = 0

        #3 cas nombre voisins >= 4
        if nb_voisin_cristal >= 4 :
            
            mask1[centre,0] = 1
            mask1[centre,2] = mask0[centre,1] + mask0[centre,2]
            mask1[centre,1] = 0
    return mask1


# -----------------------UDPDATE MASK ------------------------------


for t in range(iterations):

#       FREEZING
    a = np.where(mask_tot[:,0]==1)
    for ele in a[0] :
        mask_change = freezing(mask_tot, N, ele, kappa)
    mask_tot = mask_change

#       MELTING
    a = np.where(mask_tot[:,0]==1)
    for ele in a[0] :
        mask_change = melting(mask_tot, N, ele, mu, gamma)
    mask_tot = mask_change


    for i in range(_range_mask_tot):

#       ATTACHEMENT
        mask_change = attachement(mask_tot, N, i, alpha, beta, theta)


#       DIFFUSION
    mask_1 = np.copy(mask_change)

    for i in range(_range_mask_tot):
        
        if i%N == 0 or (i+1)%N == 0 or i < N or i > N*(N-1):    
            continue   

        elif mask_1[i,0]==1:
            continue

        elif prox_crystal(mask_1,i) != 0: # est a proximité du cristal, condition réfléchie
            mask_change[i,3] = somme_vap_voisin_cristal(mask_1, i, N) #Laplacien condition réfléchie

        else:  
            ele = alentours(mask_1,i) #
            mask_change[i,3] = somme_vap(ele) 
    
    mask_tot = mask_change
    print(t)


end = time.time()
print(f"Runtime of the program is {end - start}")


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
plot_single_lattice_custom_colors(x_hex_coords, y_hex_coords,       # Affichage total des 3 phases 
                                    face_color= final_colors,
                                    edge_color=final_colors,
                                    min_diam=1,
                                    plotting_gap=0.0,
                                    rotate_deg=0)
plt.title('Mask total')

plt.figure(2)

plot_single_lattice_custom_colors(x_hex_coords, y_hex_coords,       
                                    face_color= final_color_ice,
                                    edge_color=final_color_ice,
                                    min_diam=1,
                                    plotting_gap=0.0,
                                    rotate_deg=0)
plt.title('Mask glace')

plt.figure(3)

plot_single_lattice_custom_colors(x_hex_coords, y_hex_coords,       
                                    face_color=final_color_vapor,
                                    edge_color=final_color_vapor,
                                    min_diam=1,
                                    plotting_gap=0.0,
                                    rotate_deg=0)

plt.title('Mask vapeur')

plt.figure(4)


plot_single_lattice_custom_colors(x_hex_coords, y_hex_coords,       
                                    face_color=final_color_quasi_liquid,
                                    edge_color=final_color_quasi_liquid,
                                    min_diam=1,
                                    plotting_gap=0.0,
                                    rotate_deg=0)

plt.title(f'Mask quasi liquid')
plt.show()